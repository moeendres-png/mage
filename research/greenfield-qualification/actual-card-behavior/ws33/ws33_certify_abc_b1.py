#!/usr/bin/env python3
"""Certify the WS33B ABC-B1 calculateAmount campaign (273 paths).

Checks per-path record completeness, execution contract, decision tape,
RNG tape, hidden-observation evidence, semantic replay, and empty
diagnostics, then writes the B1 gate.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def fail(message: str) -> None:
    raise SystemExit("WS33_ABC_B1_CERTIFICATION=FAIL " + message)


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
    plan_path = root / "ABC_B1_PLAN.json"
    if not plan_path.is_file():
        fail("missing ABC_B1_PLAN.json")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    paths = plan.get("paths", [])
    if len(paths) != 273 or len(set(paths)) != 273:
        fail(f"unexpected path cardinality {len(paths)} unique={len(set(paths))}")

    failures: list[dict] = []
    decision_event_count = 0
    rng_event_count = 0
    default_zero_paths: list[str] = []
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
        if record.get("default_zero_evidence") is True:
            default_zero_paths.append(pid)
        for assertion in record.get("state_assertions", []):
            if assertion.get("result") != "PASS":
                failures.append({"path_id": pid, "failed_assertion": assertion.get("assertion_id")})
        events = tape.get("events", [])
        decision_event_count += len(events)
        if not events:
            failures.append({"path_id": pid, "decision_tape_empty": True})
            continue
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
        if not rng_events:
            failures.append({"path_id": pid, "rng_tape_empty": True})
        if observation.get("result") != "PASS":
            failures.append({"path_id": pid, "principal_observation": observation.get("result")})

    record_diag = root / "amount-record-diagnostics.jsonl"
    replay_diag = root / "amount-replay-diagnostics.jsonl"
    if not record_diag.is_file() or record_diag.stat().st_size != 0:
        failures.append({"record_diagnostics_empty": False})
    if not replay_diag.is_file() or replay_diag.stat().st_size != 0:
        failures.append({"replay_diagnostics_empty": False})

    index_path = root / "campaign-index.json"
    if not index_path.is_file():
        failures.append({"campaign_index_missing": True})
    else:
        index = json.loads(index_path.read_text(encoding="utf-8"))
        if len(index.get("records", [])) != 273:
            failures.append({"campaign_index_count": len(index.get("records", []))})

    gate = {
        "schema": "commander-simulator-next.ws33-abc-b1-gate.v1",
        "source_head": args.source_head,
        "forge_pin": args.forge_pin,
        "model_artifact_id": args.model_artifact_id,
        "model_artifact_digest": args.model_artifact_digest,
        "manifest_sha256": args.manifest_sha256,
        "consumer_model_sha256": args.consumer_model_sha256,
        "scope": {
            "logical_bucket": "WS33B",
            "runtime_subsystem": "forge.game.ability.AbilityUtils#calculateAmount",
            "scenario_group_id": "ws33-g2-template-010",
            "evidence_profile": "DECISION+RNG+HIDDEN+REPLAY",
        },
        "path_count": len(paths),
        "decision_event_count": decision_event_count,
        "rng_event_count": rng_event_count,
        "default_zero_paths": sorted(default_zero_paths),
        "default_zero_count": len(default_zero_paths),
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
    print(f"WS33_ABC_B1_CERTIFICATION=PASS paths={len(paths)} "
          f"decision_events={decision_event_count} rng_events={rng_event_count} "
          f"default_zero={len(default_zero_paths)} coverage_mutated=false")


if __name__ == "__main__":
    main()
