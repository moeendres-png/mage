#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path

OWNER = "TRIGGER_REPLACEMENT_ZONE_SBA"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--prepare-summary", type=Path, required=True)
    ap.add_argument("--changes-zone-results", type=Path, required=True)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    prep = json.loads(args.prepare_summary.read_text(encoding="utf-8"))
    if prep.get("family_path_count") != 1174:
        raise SystemExit("WS28 family count mismatch")
    if prep.get("reused_exact_ws16_child_count") != 2:
        raise SystemExit("WS28 exact WS16 reuse count mismatch")
    if prep.get("new_execution_case_count") != 1172:
        raise SystemExit("WS28 new case count mismatch")
    if prep.get("unresolved_root_count") != 0:
        raise SystemExit("WS28 unresolved production roots remain")

    rows = []
    if args.changes_zone_results.is_file():
        for line in args.changes_zone_results.read_text(encoding="utf-8").splitlines():
            if line.strip():
                cols = line.split("\t")
                rows.append(cols)
    cz_pass = sum(1 for r in rows if len(r) > 1 and r[1] == "PASS")
    cz_fail = sum(1 for r in rows if len(r) > 1 and r[1] != "PASS")

    # Critical adjudication: the current WS28 overlay produces a diagnostic
    # ChangesZone census, not WS26 Witness ABI V2 documents. Therefore none of
    # the 1172 newly assigned paths can be promoted to PASS. The two exact WS16
    # compatible child paths retain their previously adjudicated reuse only.
    gate = {
        "schema": "commander-simulator-next.ws28.gate.v1",
        "owner_family": OWNER,
        "forge_pin": FORGE_PIN,
        "tested_source_head": args.source_head,
        "tested_source_tree": args.source_tree,
        "workflow_run_id": str(args.run_id),
        "family_path_count": 1174,
        "reused_exact_ws16_child_count": 2,
        "new_execution_case_count": 1172,
        "new_v2_path_abi_pass_count": 0,
        "new_v2_path_fail_closed_count": 1172,
        "diagnostic_changes_zone_case_count": len(rows),
        "diagnostic_changes_zone_pass_count": cz_pass,
        "diagnostic_changes_zone_fail_count": cz_fail,
        "hard_gates": {
            "WS26_BOUNDARY": "PASS",
            "OWNER_PARTITION_EXACT": "PASS",
            "PRODUCTION_ROOT_PROVENANCE": "PASS",
            "EXACT_WS16_REUSE": "PASS",
            "ALL_NEW_PATHS_EXECUTED_THROUGH_ACTUAL_RULES_CORE": "FAIL_CLOSED",
            "WS26_WITNESS_ABI_V2_FOR_ALL_NEW_PATHS": "FAIL_CLOSED",
            "AUTHORITATIVE_DECISION_TAPES_WHERE_REQUIRED": "FAIL_CLOSED",
            "RNG_TAPES_WHERE_REQUIRED": "FAIL_CLOSED",
            "PRINCIPAL_SCOPED_OBSERVATION_EVIDENCE_WHERE_REQUIRED": "FAIL_CLOSED",
            "SEMANTIC_REPLAY_EVIDENCE_WHERE_REQUIRED": "FAIL_CLOSED",
            "TRIGGER_REAL_EVENT_FULL_FAMILY": "FAIL_CLOSED",
            "REPLACEMENT_REAL_EVENT_FULL_FAMILY": "FAIL_CLOSED",
            "ZONE_FULL_FAMILY": "FAIL_CLOSED",
            "SBA_REAL_CHECK_STATE_EFFECTS_FULL_FAMILY": "FAIL_CLOSED"
        },
        "failure_semantics": {
            "classification": "QUALIFICATION_HARNESS_INCOMPLETE",
            "shared_core_fix_required": False,
            "production_rules_core_defect_proven": False,
            "silent_fallback_allowed": False,
            "reason": (
                "The current branch has exact provenance and a real-event ChangesZone "
                "diagnostic census, but it does not emit WS26 Witness ABI V2 PASS "
                "documents for the 1172 newly assigned paths. Current diagnostic "
                "failures are not sufficient evidence of a Forge rules-core defect."
            )
        },
        "WS28_FAMILY_GATE": "FAIL_CLOSED",
        "WORKSTREAM_COMPLETE": False,
        "SHARED_CORE_FIX_REQUIRED": False,
        "GLOBAL_Q6_ASSERTED": False
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(gate, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("WS28_FAMILY_GATE=FAIL_CLOSED")
    print("WORKSTREAM_COMPLETE=FALSE")


if __name__ == "__main__":
    main()
