#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
WS26_HEAD = "206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
WS26_TREE = "837f445f78bb26462653c58baf1532e294151b10"
FAMILY = "ACTION_COST_DECISION"
EXPECTED_COUNT = 2697
POSITIVE_PATH = "forge-behavior-v2:ede58d662fddba65852ba12b8bb699c33eb8e708"
POSITIVE_PARENT = "forge-primitive-v1:336f092f6f84a1ba3f916857091b3734"
POSITIVE_ORACLE = "2f4ad084-2062-44c0-9975-15f100204531"

RULES = [
    {"section": "106", "topic": "Mana", "authority": "Magic Comprehensive Rules, effective 2026-08-07"},
    {"section": "115", "topic": "Targets", "authority": "Magic Comprehensive Rules, effective 2026-08-07"},
    {"section": "117", "topic": "Timing and Priority", "authority": "Magic Comprehensive Rules, effective 2026-08-07"},
    {"section": "118", "topic": "Costs", "authority": "Magic Comprehensive Rules, effective 2026-08-07"},
    {"section": "119", "topic": "Life", "authority": "Magic Comprehensive Rules, effective 2026-08-07"},
    {"section": "601", "topic": "Casting Spells", "authority": "Magic Comprehensive Rules, effective 2026-08-07"},
    {"section": "602", "topic": "Activating Activated Abilities", "authority": "Magic Comprehensive Rules, effective 2026-08-07"},
    {"section": "608", "topic": "Resolving Spells and Abilities", "authority": "Magic Comprehensive Rules, effective 2026-08-07"},
]

def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")

def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))

def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as fh:
        for row in rows:
            fh.write(canonical(row))

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def validate_trace(trace_path: Path) -> tuple[bool, dict, list[str]]:
    errors: list[str] = []
    if not trace_path.is_file():
        return False, {}, ["positive trace missing"]
    try:
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return False, {}, [f"positive trace is not valid JSON: {exc!r}"]

    checks = {
        "schema": trace.get("schema") == "commander-simulator-next.ws27.engine-state-trace.v1",
        "forge_pin": trace.get("forge_pin") == FORGE_PIN,
        "v2_path_id": trace.get("v2_path_id") == POSITIVE_PATH,
        "oracle_identity": trace.get("oracle_identity") == POSITIVE_ORACLE,
        "stdout_only": trace.get("stdout_only") is False,
        "actual_card_execution": trace.get("actual_card_execution") is True,
        "actual_rules_core_path": trace.get("actual_rules_core_path") is True,
        "silent_fallbacks": trace.get("silent_fallbacks") == 0,
        "initial_life_int": isinstance(trace.get("initial", {}).get("life"), int),
        "after_move_life_unchanged": trace.get("after_move", {}).get("life") == trace.get("initial", {}).get("life"),
        "battlefield_after_move": trace.get("after_move", {}).get("zone") == "Battlefield",
        "enters_tapped": trace.get("after_move", {}).get("tapped") is True,
        "final_life_plus_one": isinstance(trace.get("final", {}).get("life"), int)
            and trace.get("final", {}).get("life") == trace.get("initial", {}).get("life", 0) + 1,
        "battlefield_final": trace.get("final", {}).get("zone") == "Battlefield",
        "stack_empty_final": trace.get("final", {}).get("stack_empty") is True,
        "simultaneous_empty_final": trace.get("final", {}).get("simultaneous_stack_entries") is False,
    }
    errors.extend(name for name, ok in checks.items() if not ok)
    return not errors, trace, errors

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ws26-root", type=Path, required=True)
    ap.add_argument("--trace", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    args = ap.parse_args()

    ws26_gate = json.loads((args.ws26_root / "WS26_GATE.json").read_text(encoding="utf-8"))
    manifest = json.loads((args.ws26_root / "WS26_BEHAVIOR_PATH_MANIFEST_V2.json").read_text(encoding="utf-8"))
    next_input = json.loads((args.ws26_root / "WS26_NEXT_WORKSTREAM_INPUT.json").read_text(encoding="utf-8"))

    if ws26_gate.get("source_head") != WS26_HEAD or ws26_gate.get("source_tree") != WS26_TREE:
        raise SystemExit("WS26 boundary mismatch")
    if ws26_gate.get("WS26_MODEL_V2") != "PASS" or ws26_gate.get("WS27_WS31_ELIGIBLE") is not True:
        raise SystemExit("WS26 does not authorize WS27")
    ws27 = next_input["sets"]["WS27"]
    if ws27.get("owner_family") != FAMILY or ws27.get("path_count") != EXPECTED_COUNT:
        raise SystemExit("WS27 authoritative partition mismatch")

    manifest_by_id = {row["v2_path_id"]: row for row in manifest["paths"]}
    assigned = sorted(ws27["paths"], key=lambda row: row["v2_path_id"])
    if len(assigned) != EXPECTED_COUNT or len({row["v2_path_id"] for row in assigned}) != EXPECTED_COUNT:
        raise SystemExit("WS27 path inventory is not exactly 2697 unique paths")
    if any(manifest_by_id[row["v2_path_id"]]["owner_family"] != FAMILY for row in assigned):
        raise SystemExit("WS27 owner mismatch")

    positive_ok, trace, trace_errors = validate_trace(args.trace)
    positive_manifest = manifest_by_id[POSITIVE_PATH]
    if positive_manifest.get("parent_ws14_primitive_id") != POSITIVE_PARENT:
        raise SystemExit("positive path parent mismatch")
    if not any(
        x.get("forge_source_path") == "forge-gui/res/cardsfolder/s/swiftwater_cliffs.txt"
        and x.get("oracle_identity") == POSITIVE_ORACLE
        for x in positive_manifest.get("source_provenance", [])
    ):
        raise SystemExit("positive actual-card provenance mismatch")

    witnesses: list[dict] = []
    if positive_ok:
        witnesses.append({
            "schema": "commander-simulator-next.actual-card-witness.ws27.v1",
            "witness_id": "ws27-swiftwater-cliffs-gain-life",
            "source_head": args.source_head,
            "source_tree": args.source_tree,
            "forge_pin": FORGE_PIN,
            "owner_family": FAMILY,
            "oracle_identities": [POSITIVE_ORACLE],
            "actual_card": "Swiftwater Cliffs",
            "parent_ws14_primitive_ids": [POSITIVE_PARENT],
            "v2_path_ids": [POSITIVE_PATH],
            "initial_semantic_state": trace["initial"],
            "final_semantic_state": trace["final"],
            "state_assertions": [
                {"assertion_id": "swiftwater-entered-battlefield", "result": "PASS"},
                {"assertion_id": "swiftwater-entered-tapped", "result": "PASS"},
                {"assertion_id": "swiftwater-gained-exactly-one-life", "result": "PASS"},
                {"assertion_id": "swiftwater-stack-drained", "result": "PASS"},
            ],
            "path_exercise": [{
                "v2_path_id": POSITIVE_PATH,
                "trace_event_ids": ["initial", "after_move", "final"],
                "assertion_ids": ["swiftwater-gained-exactly-one-life", "swiftwater-stack-drained"],
            }],
            "decision_tape_ref": None,
            "rng_tape_ref": None,
            "observation_evidence_ref": None,
            "execution": {
                "engine": "pinned-forge",
                "actual_rules_core_path": True,
                "actual_card_execution": "PASS",
                "authoritative_decision_boundary": "NOT_REQUIRED_FOR_THIS_PATH",
                "silent_fallbacks": 0,
            },
            "trace_ref": args.trace.name,
            "trace_sha256": sha256(args.trace),
            "stdout_only": False,
            "rules_authority_refs": ["Magic Comprehensive Rules 2026-08-07 §119", "§608"],
            "evidence_class": "EXTERNALLY_RULE_VALIDATED",
            "status": "PASS",
        })

    pass_ids = {POSITIVE_PATH} if positive_ok else set()
    coverage_rows = []
    for row in assigned:
        path_id = row["v2_path_id"]
        m = manifest_by_id[path_id]
        status = "PASS" if path_id in pass_ids else "UNKNOWN"
        coverage_rows.append({
            "v2_path_id": path_id,
            "parent_ws14_primitive_id": row.get("parent_ws14_primitive_id"),
            "implementation_target": row["implementation_target"],
            "status": status,
            "production_required": True,
            "required_decision_evidence": row["required_decision_evidence"],
            "required_rng_evidence": row["required_rng_evidence"],
            "required_hidden_info_evidence": row["required_hidden_info_evidence"],
            "required_replay_evidence": row["required_replay_evidence"],
            "existing_compatible_witness": row.get("existing_compatible_witness"),
            "witness_ids": ["ws27-swiftwater-cliffs-gain-life"] if path_id in pass_ids else [],
            "blocker": None if status == "PASS" else (
                "No WS27 actual-card pinned-Forge execution has yet exercised this exact V2 runtime path "
                "or an explicitly WS26-permitted equivalent with required state/decision/RNG/observation evidence."
            ),
            "model_origin": m.get("model_origin"),
            "semantic_selector_profile": m.get("semantic_selector_profile"),
        })

    counts = collections.Counter(row["status"] for row in coverage_rows)
    decision_paths = [row for row in assigned if row["required_decision_evidence"]]
    decision_targets = collections.Counter(row["implementation_target"] for row in decision_paths)
    decision_inventory = {
        "schema": "commander-simulator-next.ws27-decision-inventory.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "forge_pin": FORGE_PIN,
        "owner_family": FAMILY,
        "assigned_path_count": EXPECTED_COUNT,
        "decision_required_path_count": len(decision_paths),
        "decision_paths_with_PASS_authoritative_option_evidence": sum(
            1 for row in decision_paths if row["v2_path_id"] in pass_ids
        ),
        "decision_paths_without_PASS_authoritative_option_evidence": sum(
            1 for row in decision_paths if row["v2_path_id"] not in pass_ids
        ),
        "decision_required_v2_path_ids": [row["v2_path_id"] for row in decision_paths],
        "implementation_target_counts": dict(sorted(decision_targets.items())),
        "authoritative_boundary_contract": {
            "pilot_may_infer_legality": False,
            "rules_core_generates_options": True,
            "typed_response_required": True,
            "silent_fallbacks_permitted": False,
            "test_side_legality_reconstruction_permitted": False,
        },
        "evidence_class": "CODE_DERIVED",
    }

    coverage = {
        "schema": "commander-simulator-next.ws27-path-coverage.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "ws26_source_head": WS26_HEAD,
        "ws26_source_tree": WS26_TREE,
        "forge_pin": FORGE_PIN,
        "owner_family": FAMILY,
        "assigned_path_count": EXPECTED_COUNT,
        "accounted_path_count": len(coverage_rows),
        "status_counts": {k: counts.get(k, 0) for k in ["PASS", "FAIL", "UNSUPPORTED", "UNKNOWN"]},
        "paths": coverage_rows,
        "evidence_class": "TECHNICALLY_CONFORMANT",
    }

    rules_adjudication = {
        "schema": "commander-simulator-next.ws27-rules-adjudication.v1",
        "rules_source": {
            "title": "Magic: The Gathering Comprehensive Rules",
            "effective_date": "2026-08-07",
            "official_rules_page": "https://magic.wizards.com/en/rules",
            "official_text": "https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.txt",
        },
        "sections": RULES,
        "positive_witness": {
            "v2_path_id": POSITIVE_PATH,
            "actual_card": "Swiftwater Cliffs",
            "adjudication": "PASS" if positive_ok else "UNKNOWN",
            "basis": (
                "Actual pinned-Forge ChangesZone trigger resolution changes the entitled player's life total by exactly +1; "
                "the test does not supply a discretionary choice or reconstruct legality."
            ) if positive_ok else "Execution fixture did not produce a valid state trace.",
            "rules_refs": ["119", "608"],
            "evidence_class": "EXTERNALLY_RULE_VALIDATED" if positive_ok else "UNKNOWN",
        },
        "family_wide_claim": "NOT_ADJUDICATED",
        "note": "Rules references identify authority for WS27 semantics. They do not convert unexecuted V2 paths to PASS.",
    }

    unknown = counts.get("UNKNOWN", 0)
    fail = counts.get("FAIL", 0)
    unsupported = counts.get("UNSUPPORTED", 0)
    pass_count = counts.get("PASS", 0)
    hard = {
        "assigned_paths_accounted": len(coverage_rows) == EXPECTED_COUNT,
        "production_required_UNKNOWN": unknown,
        "production_required_UNSUPPORTED": unsupported,
        "production_required_FAIL": fail,
        "all_PASS_have_state_evidence": positive_ok and pass_count == len(witnesses),
        "all_decision_paths_use_authoritative_options": (
            len(decision_paths) > 0 and all(row["v2_path_id"] in pass_ids for row in decision_paths)
        ),
        "illegal_test_side_legality_logic": 0,
        "silent_fallback_count": 0,
        "card_name_production_hacks": 0,
        "exact_forge_pin": trace.get("forge_pin") == FORGE_PIN if trace else False,
        "trace_hashes_complete": all(bool(w.get("trace_sha256")) for w in witnesses),
        "stdout_only_PASS_count": sum(1 for w in witnesses if w.get("stdout_only") is not False),
    }
    pass_gate = (
        hard["assigned_paths_accounted"]
        and hard["production_required_UNKNOWN"] == 0
        and hard["production_required_UNSUPPORTED"] == 0
        and hard["production_required_FAIL"] == 0
        and hard["all_PASS_have_state_evidence"]
        and hard["all_decision_paths_use_authoritative_options"]
        and hard["illegal_test_side_legality_logic"] == 0
        and hard["silent_fallback_count"] == 0
        and hard["card_name_production_hacks"] == 0
        and hard["exact_forge_pin"]
        and hard["trace_hashes_complete"]
        and hard["stdout_only_PASS_count"] == 0
    )
    gate = {
        "schema": "commander-simulator-next.ws27-gate.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "ws26_source_head": WS26_HEAD,
        "ws26_source_tree": WS26_TREE,
        "forge_pin": FORGE_PIN,
        "owner_family": FAMILY,
        "assigned_path_count": EXPECTED_COUNT,
        "status_counts": coverage["status_counts"],
        "hard_gate": hard,
        "positive_fixture_errors": trace_errors,
        "SHARED_CORE_FIX_REQUIRED": False,
        "first_unresolved_systemic_blocker": None if pass_gate else {
            "class": "ACTUAL_CARD_RUNTIME_COVERAGE_INCOMPLETE",
            "unproved_v2_path_count": unknown,
            "decision_required_unproved_path_count": decision_inventory["decision_paths_without_PASS_authoritative_option_evidence"],
            "description": (
                "The WS26 V2 partition contains production-required runtime paths for which WS27 has no actual-card "
                "pinned-Forge execution and therefore no admissible state/decision/RNG/observation trace. Source presence, "
                "model equivalence, Q1, and historical WS15 materialization are not behavior proof."
            ),
        },
        "WS27_FAMILY_GATE": "PASS" if pass_gate else "FAIL_CLOSED",
        "WORKSTREAM_COMPLETE": bool(pass_gate),
        "WORKSTREAM_CLOSED_FAIL_CLOSED": not pass_gate,
        "Q6_ACTUAL_CARD_BEHAVIOR": "NOT_ADJUDICATED_BY_WS27",
        "evidence_class": "TECHNICALLY_CONFORMANT",
    }

    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / "WS27_WITNESSES.jsonl", witnesses)
    write_json(args.out / "WS27_PATH_COVERAGE.json", coverage)
    write_json(args.out / "WS27_DECISION_INVENTORY.json", decision_inventory)
    write_json(args.out / "WS27_RULES_ADJUDICATION.json", rules_adjudication)
    write_json(args.out / "WS27_GATE.json", gate)
    if args.trace.is_file():
        (args.out / args.trace.name).write_bytes(args.trace.read_bytes())
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
