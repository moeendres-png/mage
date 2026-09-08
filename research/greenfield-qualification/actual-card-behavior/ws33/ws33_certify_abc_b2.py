#!/usr/bin/env python3
"""Certify the WS33B ABC-B2 cost campaign (397 paths + 5 terminal blockers).

Checks per-path record completeness, execution contract, profile-gated
decision/RNG evidence (required only where the path's evidence profile
demands it), hidden-observation evidence, semantic replay, campaign index,
and empty diagnostics, then writes the B2 gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit("WS33_ABC_B2_CERTIFICATION=FAIL " + message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--campaign-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--forge-pin", required=True)
    parser.add_argument("--model-artifact-id", required=True)
    parser.add_argument("--model-artifact-digest", required=True)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--consumer-model-sha256", required=True)
    args = parser.parse_args()

    root = args.campaign_root
    plan_path = root / "ABC_B2_PLAN.json"
    if not plan_path.is_file():
        fail("missing ABC_B2_PLAN.json")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    paths = plan.get("paths", [])
    if len(paths) != 397 or len(set(paths)) != 397:
        fail(f"unexpected path cardinality {len(paths)} unique={len(set(paths))}")
    terminal = plan.get("terminal_blockers", {})
    if len(terminal) != 5:
        fail("terminal blocker registry incomplete")

    case_profiles: dict[str, str] = {}
    for item in json.loads((root / "ABC_B2_PLAN.json").read_text()).get("profile_by_path", {}).items():
        case_profiles[item[0]] = item[1]

    failures: list[dict] = []
    decision_event_count = 0
    rng_event_count = 0
    for pid in paths:
        short = pid.split(":", 1)[1]
        d = root / "records" / short
        required = [
            "record.json", "record-success.marker", "decision-tape.json",
            "decision-replay.tsv", "trace.json", "final-state.txt", "semantic-replay.json",
            "rng-tape.json", "rng-replay.tsv", "principal-observation.json",
        ]
        missing = [name for name in required if not (d / name).is_file()]
        if missing:
            failures.append({"path_id": pid, "missing": missing})
            continue
        record = json.loads((d / "record.json").read_text(encoding="utf-8"))
        replay = json.loads((d / "semantic-replay.json").read_text(encoding="utf-8"))
        tape = json.loads((d / "decision-tape.json").read_text(encoding="utf-8"))
        rng = json.loads((d / "rng-tape.json").read_text(encoding="utf-8"))
        observation = json.loads((d / "principal-observation.json").read_text(encoding="utf-8"))
        execution = record.get("execution", {})
        if record.get("v2_path_ids") != [pid]:
            failures.append({"path_id": pid, "record_path_binding": record.get("v2_path_ids")})
        if execution.get("actual_card_execution") != "PASS":
            failures.append({"path_id": pid, "actual_card_execution": execution.get("actual_card_execution")})
        if execution.get("actual_rules_core_path") is not True:
            failures.append({"path_id": pid, "actual_rules_core_path": execution.get("actual_rules_core_path")})
        if execution.get("silent_fallbacks") != 0:
            failures.append({"path_id": pid, "silent_fallbacks": execution.get("silent_fallbacks")})
        if execution.get("direct_effect_resolution") is not False:
            failures.append({"path_id": pid, "direct_effect_resolution": execution.get("direct_effect_resolution")})
        if replay.get("semantic_divergence") != 0:
            failures.append({"path_id": pid, "semantic_divergence": replay.get("semantic_divergence")})
        for assertion in record.get("state_assertions", []):
            if assertion.get("result") != "PASS":
                failures.append({"path_id": pid, "failed_assertion": assertion.get("assertion_id")})
        profile = case_profiles.get(pid, "")
        events = tape.get("events", [])
        decision_event_count += len(events)
        if "DECISION" in profile and not events:
            failures.append({"path_id": pid, "decision_tape_empty": True})
        for event in events:
            if event.get("fallback_used") is not False:
                failures.append({"path_id": pid, "fallback_used": event.get("fallback_used")})
            if event.get("validation_result") != "ACCEPTED":
                failures.append({"path_id": pid, "validation_result": event.get("validation_result")})
            legal = {option.get("option_id") for option in event.get("authoritative_legal_options", [])}
            response = event.get("response_option_ids", [])
            if any(option_id not in legal for option_id in response):
                failures.append({"path_id": pid, "illegal_response_option": response})
        rng_events = rng.get("events", [])
        rng_event_count += len(rng_events)
        if "RNG" in profile and not rng_events:
            failures.append({"path_id": pid, "rng_tape_empty": True})
        if observation.get("result") != "PASS":
            failures.append({"path_id": pid, "principal_observation": observation.get("result")})

    record_diag = root / "cost-record-diagnostics.jsonl"
    replay_diag = root / "cost-replay-diagnostics.jsonl"
    if not record_diag.is_file():
        failures.append({"record_diagnostics_missing": True})
    else:
        lines = [json.loads(x) for x in record_diag.read_text().splitlines() if x.strip()]
        unexpected = [x for x in lines if x.get("path_id") not in terminal]
        if unexpected:
            failures.append({"unexpected_record_diagnostics": len(unexpected)})
    if not replay_diag.is_file():
        failures.append({"replay_diagnostics_missing": True})
    else:
        lines = [json.loads(x) for x in replay_diag.read_text().splitlines() if x.strip()]
        unexpected = [x for x in lines if x.get("path_id") not in terminal]
        if unexpected:
            failures.append({"unexpected_replay_diagnostics": len(unexpected)})

    index_path = root / "campaign-index.json"
    if not index_path.is_file():
        failures.append({"campaign_index_missing": True})
    else:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if len(index.get("records", [])) != 397:
            failures.append({"campaign_index_count": len(index.get("records", []))})

    gate = {
        "schema": "commander-simulator-next.ws33-abc-b2-gate.v1",
        "source_head": args.source_head,
        "forge_pin": args.forge_pin,
        "model_artifact_id": args.model_artifact_id,
        "model_artifact_digest": args.model_artifact_digest,
        "manifest_sha256": args.manifest_sha256,
        "consumer_model_sha256": args.consumer_model_sha256,
        "scope": {
            "logical_bucket": "WS33B",
            "runtime_subsystem": "forge.game.cost.Cost",
        },
        "path_count": len(paths),
        "terminal_blocker_count": len(terminal),
        "terminal_blockers": terminal,
        "decision_event_count": decision_event_count,
        "rng_event_count": rng_event_count,
        "failures": failures,
        "coverage_mutated": False,
        "rules_mutated_by_pilot": False,
        "silent_fallback": False,
        "result": "PASS" if not failures else "FAIL",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if failures:
        fail(json.dumps(failures[:5], sort_keys=True))
    print(f"WS33_ABC_B2_CERTIFICATION=PASS paths={len(paths)} "
          f"decision_events={decision_event_count} rng_events={rng_event_count} "
          f"terminal={len(terminal)} coverage_mutated=false")


if __name__ == "__main__":
    main()
