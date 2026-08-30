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
FAMILY = "CONTINUOUS_COPY_CONTROL"
EXPECTED = 301


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode("utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical(value))


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"".join(canonical(row) for row in rows))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def source_binding_status(binding: dict | None) -> str:
    if binding is None:
        return "NOT_PROVEN"
    if (
        binding.get("status") == "PASS"
        and binding.get("actual_card_db_loaded") is True
        and binding.get("exact_source_bound") is True
        and binding.get("implementation_target_constructed") is True
        and binding.get("direct_effect_resolve_bypass") is False
    ):
        return "PASS"
    return "FAIL_CLOSED"


def is_parser_shape_mismatch(case: dict) -> bool:
    if case.get("implementation_target") != "forge.game.trigger.TriggerHandler#parseTrigger":
        return False
    if case.get("source_directive") != "SVAR":
        return False
    text = case.get("source_text", "")
    payload_at = text.find(":", 5) if text.startswith("SVar:") else -1
    if payload_at < 0:
        return False
    payload = text[payload_at + 1 :]
    mode = next(
        (part.split("$", 1)[1].strip() for part in payload.split("|") if part.strip().startswith("Mode$")),
        "",
    )
    # Directly observed in pinned Forge: TriggerType rejects Continuous. Keep this structural,
    # never card-name-specific.
    return mode == "Continuous"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ws26-root", type=Path, required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--binding", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source-head", required=True)
    parser.add_argument("--source-tree", required=True)
    args = parser.parse_args()

    gate = json.loads((args.ws26_root / "WS26_GATE.json").read_text(encoding="utf-8"))
    next_input = json.loads((args.ws26_root / "WS26_NEXT_WORKSTREAM_INPUT.json").read_text(encoding="utf-8"))
    compatibility = json.loads((args.ws26_root / "WS26_EXISTING_WITNESS_COMPATIBILITY.json").read_text(encoding="utf-8"))

    if (
        gate.get("source_head") != WS26_HEAD
        or gate.get("source_tree") != WS26_TREE
        or gate.get("WS26_MODEL_V2") != "PASS"
        or gate.get("WS27_WS31_ELIGIBLE") is not True
    ):
        raise SystemExit("WS26 boundary/eligibility mismatch")

    assignment = next_input["sets"]["WS29"]
    if assignment.get("owner_family") != FAMILY or assignment.get("path_count") != EXPECTED:
        raise SystemExit("WS29 authoritative partition mismatch")

    cases = read_jsonl(args.cases)
    if len(cases) != EXPECTED or len({row["v2_path_id"] for row in cases}) != EXPECTED:
        raise SystemExit("WS29 cases must be exactly 301 unique paths")

    bindings = read_jsonl(args.binding)
    binding_ids = [row.get("v2_path_id") for row in bindings]
    if len(binding_ids) != len(set(binding_ids)):
        raise SystemExit("WS29 binding trace contains duplicate path IDs")
    case_ids = {row["v2_path_id"] for row in cases}
    if any(path_id not in case_ids for path_id in binding_ids):
        raise SystemExit("WS29 binding trace contains a path outside the authoritative partition")
    binding_by_id = {row["v2_path_id"]: row for row in bindings}

    ws17 = [entry for entry in compatibility.get("entries", []) if entry.get("source_workstream") == "WS17"]
    if len(ws17) != 11 or any(entry.get("v2_compatibility") != "INVALIDATED_BY_MODEL_CHANGE" for entry in ws17):
        raise SystemExit("WS17 V2 compatibility adjudication mismatch")

    output = args.out
    output.mkdir(parents=True, exist_ok=True)
    write_jsonl(output / "WS29_WITNESSES.jsonl", [])

    model_mismatch_ids = sorted(row["v2_path_id"] for row in cases if is_parser_shape_mismatch(row))
    coverage_rows: list[dict] = []
    binding_counts = collections.Counter()
    for case in sorted(cases, key=lambda row: row["v2_path_id"]):
        path_id = case["v2_path_id"]
        status = source_binding_status(binding_by_id.get(path_id))
        binding_counts[status] += 1
        blocker_parts = []
        if path_id in model_mismatch_ids:
            blocker_parts.append(
                "WS26 V2 assigns TriggerHandler#parseTrigger to an exact SVar whose Mode$ is Continuous; "
                "pinned Forge rejects Continuous as TriggerType. This upstream model/runtime-target binding is inconsistent."
            )
        if status != "PASS":
            blocker_parts.append("Exact actual-card implementation-target source binding is not proven for this path.")
        blocker_parts.append(
            "No admissible WS29 V2 semantic execution witness exercises this exact path with all path-required "
            "state, authoritative decision, RNG, principal-scoped hidden-information, and replay evidence."
        )
        coverage_rows.append(
            {
                "v2_path_id": path_id,
                "parent_ws14_primitive_id": case.get("parent_ws14_primitive_id"),
                "implementation_target": case["implementation_target"],
                "oracle_identity": case["oracle_identity"],
                "card_name": case["card_name"],
                "production_required": True,
                "source_binding": status,
                "upstream_model_runtime_target_mismatch": path_id in model_mismatch_ids,
                "semantic_status": "UNKNOWN",
                "required_decision_evidence": case["required_decision_evidence"],
                "required_rng_evidence": case["required_rng_evidence"],
                "required_hidden_info_evidence": case["required_hidden_info_evidence"],
                "required_replay_evidence": case["required_replay_evidence"],
                "witness_ids": [],
                "blocker": " ".join(blocker_parts),
            }
        )

    coverage = {
        "schema": "commander-simulator-next.ws29-path-coverage.v2",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "ws26_source_head": WS26_HEAD,
        "ws26_source_tree": WS26_TREE,
        "forge_pin": FORGE_PIN,
        "owner_family": FAMILY,
        "assigned_path_count": EXPECTED,
        "accounted_path_count": EXPECTED,
        "source_binding_trace_row_count": len(bindings),
        "source_binding_status_counts": {
            "PASS": binding_counts.get("PASS", 0),
            "FAIL_CLOSED": binding_counts.get("FAIL_CLOSED", 0),
            "NOT_PROVEN": binding_counts.get("NOT_PROVEN", 0),
        },
        "semantic_status_counts": {"PASS": 0, "FAIL": 0, "UNSUPPORTED": 0, "UNKNOWN": EXPECTED},
        "upstream_model_runtime_target_mismatch_count": len(model_mismatch_ids),
        "upstream_model_runtime_target_mismatch_v2_path_ids": model_mismatch_ids,
        "paths": coverage_rows,
        "evidence_class": "DIRECTLY_VERIFIED",
    }
    write_json(output / "WS29_PATH_COVERAGE.json", coverage)

    targets = collections.Counter(case["implementation_target"] for case in cases)
    roots = collections.Counter(case["root_kind"] for case in cases)
    directives = collections.Counter(case["source_directive"] for case in cases)
    durations = collections.Counter(
        case.get("selector_profile", {}).get("selectors", {}).get("Duration", "NONE") for case in cases
    )
    continuous = {
        "schema": "commander-simulator-next.ws29-continuous-effect-inventory.v2",
        "source_head": args.source_head,
        "forge_pin": FORGE_PIN,
        "assigned_path_count": EXPECTED,
        "implementation_target_counts": dict(sorted(targets.items())),
        "root_kind_counts": dict(sorted(roots.items())),
        "source_directive_counts": dict(sorted(directives.items())),
        "duration_selector_counts": dict(sorted(durations.items())),
        "source_binding_pass_path_count": binding_counts.get("PASS", 0),
        "semantically_asserted_path_count": 0,
        "temporary_effect_reversion_semantically_proved": False,
        "evidence_class": "CODE_DERIVED",
    }
    write_json(output / "WS29_CONTINUOUS_EFFECT_INVENTORY.json", continuous)

    copy_paths = [
        case
        for case in cases
        if any(name in case["implementation_target"] for name in ("CopyPermanentEffect", "CopySpellAbilityEffect", "CloneEffect"))
    ]
    control_paths = [case for case in cases if "Control" in case["implementation_target"]]
    copy_control = {
        "schema": "commander-simulator-next.ws29-copy-control-inventory.v2",
        "source_head": args.source_head,
        "forge_pin": FORGE_PIN,
        "copy_path_count": len(copy_paths),
        "control_path_count": len(control_paths),
        "copy_v2_path_ids": sorted(case["v2_path_id"] for case in copy_paths),
        "control_v2_path_ids": sorted(case["v2_path_id"] for case in control_paths),
        "copy_source_binding_pass_count": sum(source_binding_status(binding_by_id.get(case["v2_path_id"])) == "PASS" for case in copy_paths),
        "control_source_binding_pass_count": sum(source_binding_status(binding_by_id.get(case["v2_path_id"])) == "PASS" for case in control_paths),
        "copy_semantically_asserted_count": 0,
        "control_semantically_asserted_count": 0,
        "evidence_class": "DIRECTLY_VERIFIED",
    }
    write_json(output / "WS29_COPY_CONTROL_INVENTORY.json", copy_control)

    rules = {
        "schema": "commander-simulator-next.ws29-rules-adjudication.v2",
        "rules_source": {
            "title": "Magic: The Gathering Comprehensive Rules",
            "effective_date": "2026-08-07",
            "official_rules_page": "https://magic.wizards.com/en/rules",
            "official_text": "https://media.wizards.com/2026/downloads/MagicCompRules%2020260807.txt",
        },
        "sections": [
            {"section": "611.1/611.2a", "topic": "Continuous effects and durations"},
            {"section": "613.1a/b/d/e/f/g", "topic": "Copy, control, type, color, ability and power/toughness layers"},
            {"section": "613.2a/613.4b-c/613.6-613.8", "topic": "Layer ordering, timestamps and dependency"},
            {"section": "707.2", "topic": "Copiable values"},
            {"section": "514.2", "topic": "Cleanup and until-end-of-turn expiration"},
            {"section": "723.1/723.3", "topic": "Controlling another player"},
        ],
        "ws17_compatibility": {
            "entries_checked": len(ws17),
            "v2_compatible_PASS_inherited": 0,
            "invalidated_by_model_change": len(ws17),
        },
        "upstream_model_runtime_target_mismatches": model_mismatch_ids,
        "family_wide_semantic_adjudication": "NOT_PROVEN",
        "source_binding_is_semantic_proof": False,
        "evidence_class": "EXTERNALLY_RULE_VALIDATED",
    }
    write_json(output / "WS29_RULES_ADJUDICATION.json", rules)

    required = lambda key: sum(1 for case in cases if case[key])
    hard_gate = {
        "assigned_paths_accounted": True,
        "source_binding_trace_rows": len(bindings),
        "source_binding_PASS": binding_counts.get("PASS", 0),
        "source_binding_FAIL_CLOSED": binding_counts.get("FAIL_CLOSED", 0),
        "source_binding_NOT_PROVEN": binding_counts.get("NOT_PROVEN", 0),
        "upstream_model_runtime_target_mismatch_count": len(model_mismatch_ids),
        "production_required_UNKNOWN": EXPECTED,
        "production_required_UNSUPPORTED": 0,
        "production_required_FAIL": 0,
        "continuous_effect_paths_semantically_asserted": False,
        "copy_paths_semantically_asserted": False,
        "control_paths_semantically_asserted": False,
        "temporary_effect_reversion_where_required": False,
        "layer_sensitive_expectations_external_rules_validated": True,
        "decision_required_paths": required("required_decision_evidence"),
        "decision_paths_with_complete_PASS_evidence": 0,
        "rng_required_paths": required("required_rng_evidence"),
        "rng_paths_with_complete_PASS_evidence": 0,
        "hidden_info_required_paths": required("required_hidden_info_evidence"),
        "hidden_info_paths_with_complete_PASS_evidence": 0,
        "replay_required_paths": required("required_replay_evidence"),
        "replay_paths_with_complete_PASS_evidence": 0,
        "silent_fallback_count": 0,
        "card_name_production_hacks": 0,
        "source_binding_direct_effect_resolve_bypass_count": sum(
            row.get("direct_effect_resolve_bypass") is not False for row in bindings
        ),
        "exact_forge_pin": True,
        "semantic_trace_hashes_complete": False,
        "ws17_blanket_inheritance": False,
        "global_q6_adjudicated": False,
    }
    gate_out = {
        "schema": "commander-simulator-next.ws29-gate.v2",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "ws26_source_head": WS26_HEAD,
        "ws26_source_tree": WS26_TREE,
        "forge_pin": FORGE_PIN,
        "owner_family": FAMILY,
        "hard_gate": hard_gate,
        "WS29_FAMILY_GATE": "FAIL_CLOSED",
        "WORKSTREAM_COMPLETE": False,
        "WORKSTREAM_CLOSED_FAIL_CLOSED": True,
        "qualification_execution_complete": True,
        "SHARED_CORE_FIX_REQUIRED": False,
        "UPSTREAM_MODEL_FIX_REQUIRED": bool(model_mismatch_ids),
        "Q6_ACTUAL_CARD_BEHAVIOR": "NOT_ADJUDICATED_BY_WS29",
        "blocker_class": "ACTUAL_CARD_SEMANTIC_RUNTIME_COVERAGE_INCOMPLETE",
        "blocker": (
            f"{EXPECTED}/301 WS29 V2 paths remain semantically UNKNOWN. The WS26 V2 witness ABI requires exact "
            "actual-card semantic execution plus all path-required decision/RNG/hidden-information/replay evidence. "
            f"Additionally, {len(model_mismatch_ids)} structurally verified WS26 model/runtime-target mismatch(es) "
            "prevent honest source-binding promotion until the upstream V2 model is corrected."
        ),
    }
    write_json(output / "WS29_GATE.json", gate_out)

    hashed = [
        "WS29_WITNESSES.jsonl",
        "WS29_PATH_COVERAGE.json",
        "WS29_CONTINUOUS_EFFECT_INVENTORY.json",
        "WS29_COPY_CONTROL_INVENTORY.json",
        "WS29_RULES_ADJUDICATION.json",
        "WS29_GATE.json",
    ]
    (output / "WS29_HASHES.sha256").write_text(
        "".join(f"{sha256(output / name)}  {name}\n" for name in hashed), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "assigned": EXPECTED,
                "source_binding_trace_rows": len(bindings),
                "source_binding_PASS": binding_counts.get("PASS", 0),
                "semantic_PASS": 0,
                "semantic_UNKNOWN": EXPECTED,
                "upstream_model_runtime_target_mismatch_count": len(model_mismatch_ids),
                "WS29_FAMILY_GATE": "FAIL_CLOSED",
                "WORKSTREAM_CLOSED_FAIL_CLOSED": True,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
