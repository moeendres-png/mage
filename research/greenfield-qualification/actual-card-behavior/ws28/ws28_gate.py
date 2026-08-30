#!/usr/bin/env python3
"""Materialize WS28's fail-closed closure evidence.

This is intentionally a gate materializer, not a witness synthesizer. A
missing actual-card execution is FAIL_CLOSED for the exact V2 path; source
metadata and generic event drivers can never create a PASS witness here.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from collections import Counter
from pathlib import Path

OWNER = "TRIGGER_REPLACEMENT_ZONE_SBA"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
NEW_PATHS, REUSED_PATHS = 1172, 2
FAMILY_PATHS = NEW_PATHS + REUSED_PATHS


def b64d(value: str) -> str:
    return base64.b64decode(value).decode("utf-8") if value else ""


def read_cases(path: Path) -> list[dict]:
    cases: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line:
            continue
        c = line.split("\t")
        if len(c) != 22:
            raise SystemExit(f"WS28 case TSV ABI mismatch at line {line_no}: {len(c)}")
        cases.append({
            "v2_path_id": c[0], "parent_ws14_primitive_id": c[1],
            "oracle_identity": c[2], "oracle_name": b64d(c[3]),
            "required_decision_evidence": c[7] == "1", "required_rng_evidence": c[8] == "1",
            "required_hidden_info_evidence": c[9] == "1", "required_replay_evidence": c[10] == "1",
            "forge_source_path": b64d(c[11]), "source_line": int(c[12]),
            "root_kind": c[16], "root_record": b64d(c[17]),
        })
    if len(cases) != NEW_PATHS or len({c["v2_path_id"] for c in cases}) != NEW_PATHS:
        raise SystemExit("WS28 exact new-path case count mismatch")
    return cases


def changes_zone_counts(path: Path) -> tuple[int, int, int]:
    if not path.is_file():
        return 0, 0, 0
    rows = [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line]
    return len(rows), sum(r[1] == "PASS" for r in rows), sum(r[1] != "PASS" for r in rows)


def category(case: dict) -> str:
    # Inventory only, never an execution classifier or semantic proof.
    raw = case["root_record"]
    if case["root_kind"] == "R" or "Replacement" in raw:
        return "replacement"
    if case["root_kind"] == "T" or "Trigger" in raw:
        return "trigger"
    if "StateBased" in raw or "SBA" in raw:
        return "sba"
    return "zone_or_other_owner_path"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare-summary", type=Path, required=True)
    ap.add_argument("--cases", type=Path, required=True)
    ap.add_argument("--changes-zone-results", type=Path, required=True)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out-dir", type=Path, required=True)
    args = ap.parse_args()

    prep = json.loads(args.prepare_summary.read_text(encoding="utf-8"))
    for key, expected in {"family_path_count": FAMILY_PATHS, "reused_exact_ws16_child_count": REUSED_PATHS,
                          "new_execution_case_count": NEW_PATHS, "unresolved_root_count": 0}.items():
        if prep.get(key) != expected:
            raise SystemExit(f"WS28 preparation invariant failed: {key}")
    cases = read_cases(args.cases)
    diagnostic_total, diagnostic_pass, diagnostic_fail = changes_zone_counts(args.changes_zone_results)
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    # Empty by design: do not synthesize an ABI V2 witness for an unexecuted path.
    (out / "WS28_WITNESSES.jsonl").write_text("", encoding="utf-8")
    required = Counter()
    inventory = {"trigger": [], "replacement": [], "zone_or_other_owner_path": [], "sba": []}
    coverage = []
    for case in cases:
        group = category(case)
        required["decision"] += case["required_decision_evidence"]
        required["rng"] += case["required_rng_evidence"]
        required["hidden"] += case["required_hidden_info_evidence"]
        required["replay"] += case["required_replay_evidence"]
        entry = {
            "v2_path_id": case["v2_path_id"], "oracle_identity": case["oracle_identity"],
            "oracle_name": case["oracle_name"], "parent_ws14_primitive_id": case["parent_ws14_primitive_id"],
            "inventory_category": group, "status": "FAIL_CLOSED",
            "reason": "no WS26 Witness ABI V2 actual-card runtime witness materialized",
            "required_evidence": {"decision": case["required_decision_evidence"], "rng": case["required_rng_evidence"],
                                  "hidden_observation": case["required_hidden_info_evidence"], "semantic_replay": case["required_replay_evidence"]},
            "source_provenance": {"forge_source_path": case["forge_source_path"], "source_line": case["source_line"]},
        }
        coverage.append(entry)
        inventory[group].append({k: entry[k] for k in ("v2_path_id", "oracle_identity", "oracle_name", "status", "reason")})
    (out / "WS28_PATH_COVERAGE.json").write_text(json.dumps({
        "schema": "commander-simulator-next.ws28.path-coverage.v1", "owner_family": OWNER,
        "family_path_count": FAMILY_PATHS, "exact_ws16_reuse_count": REUSED_PATHS, "new_path_count": NEW_PATHS,
        "new_abi_v2_pass_count": 0, "new_fail_closed_count": NEW_PATHS, "paths": coverage,
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    for group, filename in (("trigger", "WS28_TRIGGER_INVENTORY.json"), ("replacement", "WS28_REPLACEMENT_INVENTORY.json")):
        (out / filename).write_text(json.dumps({"schema": "commander-simulator-next.ws28.inventory.v1", "kind": group,
            "classification": "SOURCE_INVENTORY_ONLY_NOT_RUNTIME_PROOF", "count": len(inventory[group]), "paths": inventory[group]}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    zone_sba = inventory["zone_or_other_owner_path"] + inventory["sba"]
    (out / "WS28_ZONE_SBA_INVENTORY.json").write_text(json.dumps({"schema": "commander-simulator-next.ws28.inventory.v1", "kind": "zone_sba",
        "classification": "SOURCE_INVENTORY_ONLY_NOT_RUNTIME_PROOF", "count": len(zone_sba), "paths": zone_sba}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (out / "WS28_RULES_ADJUDICATION.json").write_text(json.dumps({"schema": "commander-simulator-next.ws28.rules-adjudication.v1", "status": "NOT_MATERIALIZED",
        "reason": "No path is promoted without a path-specific current official-rules adjudication and ABI V2 witness.", "official_rules_claims_made": 0}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    gate = {
        "schema": "commander-simulator-next.ws28.gate.v2", "owner_family": OWNER, "forge_pin": FORGE_PIN,
        "tested_source_head": args.source_head, "tested_source_tree": args.source_tree, "workflow_run_id": str(args.run_id),
        "family_path_count": FAMILY_PATHS, "reused_exact_ws16_child_count": REUSED_PATHS, "new_execution_case_count": NEW_PATHS,
        "new_v2_path_abi_pass_count": 0, "new_v2_path_fail_closed_count": NEW_PATHS, "required_evidence_path_counts": dict(required),
        "diagnostic_changes_zone_case_count": diagnostic_total, "diagnostic_changes_zone_pass_count": diagnostic_pass, "diagnostic_changes_zone_fail_count": diagnostic_fail,
        "hard_gates": {"WS26_BOUNDARY": "PASS", "OWNER_PARTITION_EXACT": "PASS", "PRODUCTION_ROOT_PROVENANCE": "PASS", "EXACT_WS16_REUSE": "PASS",
          "ALL_NEW_PATHS_EXECUTED_THROUGH_ACTUAL_RULES_CORE": "FAIL_CLOSED", "WS26_WITNESS_ABI_V2_FOR_ALL_NEW_PATHS": "FAIL_CLOSED",
          "AUTHORITATIVE_DECISION_TAPES_WHERE_REQUIRED": "FAIL_CLOSED", "RNG_TAPES_WHERE_REQUIRED": "FAIL_CLOSED",
          "PRINCIPAL_SCOPED_OBSERVATION_EVIDENCE_WHERE_REQUIRED": "FAIL_CLOSED", "SEMANTIC_REPLAY_EVIDENCE_WHERE_REQUIRED": "FAIL_CLOSED",
          "TRIGGER_REAL_EVENT_FULL_FAMILY": "FAIL_CLOSED", "REPLACEMENT_REAL_EVENT_FULL_FAMILY": "FAIL_CLOSED", "ZONE_FULL_FAMILY": "FAIL_CLOSED", "SBA_REAL_CHECK_STATE_EFFECTS_FULL_FAMILY": "FAIL_CLOSED"},
        "failure_semantics": {"classification": "QUALIFICATION_HARNESS_INCOMPLETE", "shared_core_fix_required": False,
          "production_rules_core_defect_proven": False, "silent_fallback_allowed": False,
          "reason": "No generic event census or source inventory is accepted as an actual-card semantic witness."},
        "WS28_FAMILY_GATE": "FAIL_CLOSED", "WORKSTREAM_COMPLETE": False, "SHARED_CORE_FIX_REQUIRED": False, "GLOBAL_Q6_ASSERTED": False,
    }
    (out / "WS28_GATE.json").write_text(json.dumps(gate, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    inputs = sorted(p for p in out.iterdir() if p.name != "WS28_HASHES.sha256")
    (out / "WS28_HASHES.sha256").write_text("".join(f"{digest(p)}  {p.name}\n" for p in inputs), encoding="utf-8")
    print("WS28_FAMILY_GATE=FAIL_CLOSED")
    print("WORKSTREAM_COMPLETE=FALSE")


if __name__ == "__main__":
    main()
