#!/usr/bin/env python3
"""Collect WS07 Forge semantic assertions into fail-closed machine-readable evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ALLOWED_EVIDENCE = {"TECHNICALLY_CONFORMANT", "DIRECTLY_VERIFIED", "CODE_DERIVED"}
AUXILIARY_IDS = {
    "SUBSET_2P", "SUBSET_3P", "SUBSET_4P", "SUBSET_5P",
    "MANDATORY_LONDON_MULLIGAN", "MANDATORY_STARTING_PLAYER",
}
FORBIDDEN_UNRECOVERED_REGRESSIONS = {
    "Hedron Archive", "Glissa Sunslayer", "Slip Out the Back", "Void Rend"
}


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain an object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no} must contain an object")
        rows.append(value)
    return rows


def merge_rows(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        rid = row.get("id")
        if not isinstance(rid, str) or not rid:
            raise ValueError("raw semantic row missing id")
        current = by_id.get(rid)
        if current is None:
            by_id[rid] = dict(row)
            continue
        # Multiple semantic scenarios may substantiate one broad A-T class.
        if current.get("result") != "PASS" or row.get("result") != "PASS":
            raise ValueError(f"duplicate non-PASS semantic rows for {rid}")
        current.setdefault("semantic_assertions", []).extend(row.get("semantic_assertions", []))
        current["observed_state"] = str(current.get("observed_state", "")) + " | " + str(row.get("observed_state", ""))
        current["scenario_source"] = str(current.get("scenario_source", "")) + ";" + str(row.get("scenario_source", ""))
    return by_id


def normalized_requirement(definition: dict[str, Any], row: dict[str, Any] | None, matrix_path: str) -> dict[str, Any]:
    base = {
        "id": definition["id"],
        "definition": definition["definition"],
        "requirement_source": matrix_path,
        "source_head": definition.get("source_head"),
        "source_tree": definition.get("source_tree"),
        "external_pins": definition.get("external_pins", {}),
    }
    if row is None:
        return {
            **base,
            "scenario_source": None,
            "player_count": None,
            "initial_state": None,
            "decisions": None,
            "semantic_assertions": [],
            "observed_state": None,
            "result": "NOT_EXECUTED_IN_WS07",
            "evidence_class": "UNKNOWN",
            "blocker": "No WS07-owned semantic scenario emitted for this broad A-T class; no PASS inferred from source presence or process exit.",
        }
    return {**base, **row}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--a-matrix", type=Path, required=True)
    ap.add_argument("--c-matrix", type=Path, required=True)
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--harness", type=Path, action="append", default=[])
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    ap.add_argument("--forge-pin", required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--a-output", type=Path, required=True)
    ap.add_argument("--c-output", type=Path, required=True)
    args = ap.parse_args()

    a_matrix = load_json(args.a_matrix)
    c_matrix = load_json(args.c_matrix)
    a_defs = a_matrix.get("classes")
    c_defs = c_matrix.get("definitions")
    if not isinstance(a_defs, list) or not isinstance(c_defs, list):
        raise ValueError("matrix structure mismatch")

    a_ids = [row.get("id") for row in a_defs]
    c_ids = [row.get("id") for row in c_defs]
    expected_a = [chr(ord("A") + i) for i in range(20)]
    expected_c = [f"C{i:02d}" for i in range(1, 23)]
    a_defined = len(a_defs) == 20 and a_ids == expected_a
    c_defined = len(c_defs) == 22 and c_ids == expected_c

    raw_rows = load_jsonl(args.raw)
    by_id = merge_rows(raw_rows)
    allowed_ids = set(expected_a) | set(expected_c) | AUXILIARY_IDS
    invented_ids = sorted(set(by_id) - allowed_ids)

    row_errors: list[str] = []
    process_exit_only = 0
    for rid, row in by_id.items():
        if row.get("result") != "PASS":
            row_errors.append(f"{rid}: raw harness row is not PASS")
            continue
        assertions = row.get("semantic_assertions")
        if not isinstance(assertions, list) or not assertions or not all(isinstance(x, str) and x.strip() for x in assertions):
            row_errors.append(f"{rid}: PASS lacks semantic assertions")
        if not isinstance(row.get("observed_state"), str) or not row["observed_state"].strip():
            row_errors.append(f"{rid}: PASS lacks observed engine state")
        if row.get("evidence_class") not in ALLOWED_EVIDENCE:
            row_errors.append(f"{rid}: invalid semantic evidence class")
        if row.get("assertion_kind") == "PROCESS_EXIT":
            process_exit_only += 1

    forbidden_mentions: list[str] = []
    for harness in args.harness:
        text = harness.read_text(encoding="utf-8")
        for name in FORBIDDEN_UNRECOVERED_REGRESSIONS:
            if name in text:
                forbidden_mentions.append(f"{harness}:{name}")

    c_pass_4p = all(
        cid in by_id
        and by_id[cid].get("result") == "PASS"
        and by_id[cid].get("player_count") == 4
        for cid in expected_c
    )
    mandatory_aux = ["MANDATORY_LONDON_MULLIGAN", "MANDATORY_STARTING_PLAYER", "J", "C19", "P", "R"]
    mandatory_4p = c_pass_4p and all(
        mid in by_id and by_id[mid].get("result") == "PASS" and by_id[mid].get("player_count") == 4
        for mid in mandatory_aux
    )
    subset_gates = {
        f"{count}P_conformance_required_subset": (
            f"SUBSET_{count}P" in by_id
            and by_id[f"SUBSET_{count}P"].get("result") == "PASS"
            and by_id[f"SUBSET_{count}P"].get("player_count") == count
        )
        for count in (2, 3, 4, 5)
    }

    gates: dict[str, Any] = {
        "A_T_defined": 20 if a_defined else len(a_defs),
        "C01_C22_defined": 22 if c_defined else len(c_defs),
        "source_authority_missing_tests_invented": len(invented_ids) + len(forbidden_mentions),
        "all_mandatory_4P_commander_scenarios": "PASS" if mandatory_4p else "FAIL",
        **{k: "PASS" if v else "FAIL" for k, v in subset_gates.items()},
        "process_exit_only_passes_counted_as_semantic": process_exit_only,
        "raw_semantic_row_errors": len(row_errors),
        "forge_pin_matches": args.forge_pin == "8c7e9afb8e6caee88644b94e25da5852e36f8928",
    }
    q5 = (
        a_defined
        and c_defined
        and gates["source_authority_missing_tests_invented"] == 0
        and mandatory_4p
        and all(subset_gates.values())
        and process_exit_only == 0
        and not row_errors
        and gates["forge_pin_matches"]
    )
    gates["Q5_COMMANDER_MULTIPLAYER"] = "PASS" if q5 else "FAIL"

    a_results = [normalized_requirement(d, by_id.get(d["id"]), args.a_matrix.name) for d in a_defs]
    c_results = [normalized_requirement(d, by_id.get(d["id"]), args.c_matrix.name) for d in c_defs]

    a_executed = {
        **a_matrix,
        "qualification_source_head": args.source_head,
        "qualification_source_tree": args.source_tree,
        "forge_pin": args.forge_pin,
        "ws07_results": a_results,
        "production_qualified": all(r["result"] == "PASS" for r in a_results),
        "qualification_status": "PASS" if all(r["result"] == "PASS" for r in a_results) else "PARTIAL",
        "note": "Broad A-T status is not promoted by Q5 unless that A-T class has its own semantic row.",
    }
    c_executed = {
        **c_matrix,
        "qualification_source_head": args.source_head,
        "qualification_source_tree": args.source_tree,
        "forge_pin": args.forge_pin,
        "ws07_results": c_results,
        "production_qualified": q5,
        "qualification_status": "PASS" if q5 else "FAIL",
    }
    result = {
        "schema": "commander-simulator-next.ws07-rules-commander-conformance.v1",
        "status": "PASS" if q5 else "FAIL",
        "workstream_complete": q5,
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "audit_base_sha": "c0e42fb42c4a603aff4a76b1284f8271c12bfd42",
        "forge_pin": args.forge_pin,
        "raw_semantic_rows": len(raw_rows),
        "gates": gates,
        "row_errors": row_errors,
        "invented_ids": invented_ids,
        "forbidden_unrecovered_regression_mentions": forbidden_mentions,
        "a_t": a_results,
        "c01_c22": c_results,
        "auxiliary": [by_id[x] for x in sorted(AUXILIARY_IDS) if x in by_id],
        "evidence_class": "TECHNICALLY_CONFORMANT" if q5 else "UNKNOWN",
    }

    for path, payload in ((args.output, result), (args.a_output, a_executed), (args.c_output, c_executed)):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({"status": result["status"], "gates": gates, "row_errors": row_errors}, sort_keys=True))
    return 0 if q5 else 2


if __name__ == "__main__":
    raise SystemExit(main())
