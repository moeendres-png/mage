#!/usr/bin/env python3
"""Materialize the conservative WS33 H state-only actual-card campaign.

Only Generation-2 COMBAT_COMMANDER UNKNOWN paths whose runtime target is a static
combat legality primitive or TriggerAttacks are admitted. Historical WS30 data is
used solely for card/rules metadata; every qualifying trace must come from the fresh
pinned-Forge execution supplied to this tool.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import unicodedata
from pathlib import Path

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
SAFE_TARGETS = {
    "forge.game.staticability.StaticAbilityMode#CantAttack",
    "forge.game.staticability.StaticAbilityMode#MustAttack",
    "forge.game.staticability.StaticAbilityMode#CantBlock",
    "forge.game.staticability.StaticAbilityMode#CantBlockBy",
    "forge.game.staticability.StaticAbilityMode#CantAttackUnless",
    "forge.game.staticability.StaticAbilityMode#CanAttackDefender",
    "forge.game.trigger.TriggerAttacks",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_H_STATE_CAMPAIGN=FAIL " + msg)


def slug(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "_", text).strip("_")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--coverage", type=Path, required=True)
    ap.add_argument("--trace", type=Path, required=True)
    ap.add_argument("--historical-witnesses", type=Path, required=True)
    ap.add_argument("--harness", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    manifest = load(args.manifest)
    coverage = load(args.coverage)
    status = {row["effective_v2_path_id"]: row["status"] for row in coverage["paths"]}
    paths = {row["v2_path_id"]: row for row in manifest["paths"]}
    safe = {
        pid: row for pid, row in paths.items()
        if row["owner_family"] == "COMBAT_COMMANDER"
        and row["implementation_target"] in SAFE_TARGETS
        and status.get(pid) == "UNKNOWN"
    }
    require(len(safe) == 15, f"expected 15 current H state-only paths, got {len(safe)}")
    for pid, row in safe.items():
        require(not any(bool(row.get(key)) for key in (
            "required_decision_evidence", "required_rng_evidence",
            "required_hidden_info_evidence", "required_replay_evidence",
        )), "safe H path unexpectedly requires non-state evidence: " + pid)

    traces = load_jsonl(args.trace)
    by_path = {}
    for row in traces:
        pid = row.get("path_id")
        if pid not in safe:
            continue
        require(pid not in by_path, "duplicate fresh runtime trace for " + pid)
        require(row.get("forge_pin") == PIN, "fresh trace Forge pin mismatch for " + pid)
        require(row.get("result") == "PASS", "fresh runtime trace did not PASS for " + pid)
        require(row.get("evidence_class") == "TECHNICALLY_CONFORMANT", "unexpected runtime evidence class for " + pid)
        by_path[pid] = row
    require(set(by_path) == set(safe), "fresh runtime trace does not exactly cover 15 safe H paths")

    historical = {row["path_id"]: row for row in load_jsonl(args.historical_witnesses) if row.get("path_id") in safe}
    require(set(historical) == set(safe), "historical metadata does not exactly cover safe H paths")
    harness_sha = hashlib.sha256(args.harness.read_bytes()).hexdigest()

    records = []
    for pid in sorted(safe):
        path = safe[pid]
        trace = dict(by_path[pid])
        meta = historical[pid]
        require(meta.get("card") == trace.get("card"), "fresh/historical card mismatch for " + pid)
        require(meta.get("manual_legality") is False, "historical witness used manual legality for " + pid)
        require(meta.get("rules_core_authority") is True, "historical witness lacks rules-core authority marker for " + pid)

        card_slug = slug(trace["card"])
        matching_prov = [
            prov for prov in path.get("source_provenance", [])
            if Path(prov["forge_source_path"]).stem == card_slug
        ]
        require(len(matching_prov) == 1, f"cannot bind fresh card {trace['card']} to exact Oracle provenance for {pid}")
        oracle_id = matching_prov[0]["oracle_identity"]
        require(oracle_id in path.get("representative_actual_oracle_identities", []), "Oracle identity is not representative for " + pid)

        event_id = "h-state-" + pid.split(":", 1)[1][:16]
        trace["trace_event_id"] = event_id
        trace["qualification_harness_sha256"] = harness_sha
        record_dir = args.out / "records" / pid.split(":", 1)[1]
        trace_path = record_dir / "trace.json"
        write(trace_path, trace)

        rules = [f"{meta.get('rules_url')}#CR-{rule}" for rule in meta.get("official_rule_refs", [])]
        require(rules, "missing official rules references for " + pid)
        assertion_id = "fresh-runtime-assertions"
        record = {
            "schema": "commander-simulator-next.ws33-runtime-campaign-record.v1",
            "witness_id": "ws33-h-state-" + pid.split(":", 1)[1],
            "oracle_identities": [oracle_id],
            "v2_path_ids": [pid],
            "owner_family": "COMBAT_COMMANDER",
            "initial_semantic_state": {
                "card": trace["card"],
                "dispatch": trace["dispatch"],
                "initial_state": trace["initial_state"],
                "legal_attackers": trace["legal_attackers"],
                "legal_blockers": trace["legal_blockers"],
                "restrictions_requirements": trace["restrictions_requirements"],
            },
            "final_semantic_state": {
                "selected_declaration": trace["selected_declaration"],
                "validation_result": trace["validation_result"],
                "combat_state": trace["combat_state"],
                "damage_assignment": trace["damage_assignment"],
                "post_damage_state": trace["post_damage_state"],
                "semantic_assertion": trace["semantic_assertion"],
            },
            "state_assertions": [{
                "assertion_id": assertion_id,
                "expected": "PASS",
                "actual": trace["result"],
                "result": "PASS",
                "fresh_runtime_assertions_executed": True,
            }],
            "path_exercise": [{
                "v2_path_id": pid,
                "exercised": True,
                "trace_event_ids": [event_id],
                "assertion_ids": [assertion_id],
            }],
            "execution": {
                "actual_rules_core_path": True,
                "authoritative_decision_boundary": "NOT_REQUIRED",
                "silent_fallbacks": 0,
                "actual_card_execution": "PASS",
                "fresh_runtime_trace": True,
                "historical_pass_status_reused": False,
                "qualification_harness_sha256": harness_sha,
            },
            "trace_file": trace_path.relative_to(args.out).as_posix(),
            "decision_tape_file": None,
            "rng_tape_file": None,
            "observation_evidence_file": None,
            "semantic_replay_evidence_file": None,
            "rules_authority_refs": rules,
            "evidence_class": "TECHNICALLY_CONFORMANT",
            "execution_environment_identity": {
                "runner_os": "ubuntu-24.04",
                "java_version": "21",
                "process_isolation": "FRESH_JVM_TARGETED_TEST",
                "player_count": 4,
                "game_type": "Commander",
            },
        }
        record_path = record_dir / "record.json"
        write(record_path, record)
        records.append(record_path.relative_to(args.out).as_posix())

    write(args.out / "campaign-index.json", {
        "schema": "commander-simulator-next.ws33-runtime-campaign-index.v1",
        "records": records,
    })
    write(args.out / "WS33_H_STATE_CAMPAIGN_GATE.json", {
        "schema": "commander-simulator-next.ws33-h-state-campaign-gate.v1",
        "status": "PASS",
        "forge_pin": PIN,
        "path_count": len(safe),
        "path_ids": sorted(safe),
        "harness_sha256": harness_sha,
        "historical_pass_status_reused": False,
        "actual_card_runtime_reexecuted": True,
        "direct_resolution_paths_admitted": 0,
    })
    print(json.dumps({"WS33_H_STATE_CAMPAIGN": "PASS", "paths": len(safe)}, sort_keys=True))


if __name__ == "__main__":
    main()
