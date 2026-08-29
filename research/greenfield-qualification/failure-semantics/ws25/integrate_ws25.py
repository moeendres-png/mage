#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

CATEGORIES = [
    "SUCCESS", "PLAYER_CANCELLED", "ACTION_NOT_COMPLETABLE", "ILLEGAL_RESPONSE",
    "MALFORMED_RESPONSE", "STALE_RESPONSE", "WRONG_ACTOR", "TIMEOUT",
    "UNSUPPORTED_DECISION_PATH", "UNSUPPORTED_RULES_PATH", "ENGINE_FAILURE",
    "TRANSPORT_FAILURE", "PROCESS_FAILURE", "REPLAY_DIVERGENCE",
    "HIDDEN_INFO_VIOLATION", "CARD_BEHAVIOR_FAILURE",
]
RETAINED_WS12 = {
    "SUCCESS", "PLAYER_CANCELLED", "ILLEGAL_RESPONSE", "MALFORMED_RESPONSE",
    "STALE_RESPONSE", "WRONG_ACTOR", "TIMEOUT", "UNSUPPORTED_DECISION_PATH",
    "PROCESS_FAILURE",
}
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def find_one(root: Path, name: str) -> Path:
    hits = sorted(p for p in root.rglob(name) if p.is_file())
    if len(hits) != 1:
        raise SystemExit(f"expected exactly one {name} under {root}, got {hits}")
    return hits[0]


def find_ws21_trace(root: Path, category: str) -> tuple[Path, dict[str, Any]]:
    matches: list[tuple[Path, dict[str, Any]]] = []
    for path in root.rglob("fault-trace.jsonl"):
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("category") == category:
                matches.append((path, row))
    if len(matches) != 1:
        raise SystemExit(f"expected one WS21 trace for {category}, got {len(matches)}")
    return matches[0]


def retained_row(base: dict[str, Any], contract: dict[str, Any], category: str) -> dict[str, Any]:
    row = next(r for r in base["category_matrix"] if r["outcome"]["category"] == category)
    checks = row["checks"]
    if row["classification"] not in {"PASS", "CONDITIONAL_PASS"}:
        raise SystemExit(f"retained WS12 category no longer qualifying: {category}")
    if not checks.get("exact_typed_category") or not checks.get("public_payload_schema_valid"):
        raise SystemExit(f"retained WS12 typed/schema gate failed: {category}")
    if not checks.get("failure_payload_hidden_information_safe"):
        raise SystemExit(f"retained WS12 hidden-info gate failed: {category}")
    if not checks.get("no_pass_cancel_default_random_first_or_skip_fallback"):
        raise SystemExit(f"retained WS12 fallback gate failed: {category}")
    return {
        "category": category,
        "contract_production_reachable": bool(contract["x-categories"][category]["production_reachable"]),
        "production_reachable": True,
        "reachable_boundary": row["production_binding"],
        "detector_adapter": row["production_binding"],
        "typed_result": category,
        "state_commit_semantics": contract["x-categories"][category]["state_commit"],
        "observed_state_committed": row["outcome"]["state_committed"],
        "hidden_info_safe": True,
        "fallback_absent": True,
        "evidence_source": "WS12",
        "evidence_class": row["evidence_class"],
        "classification": row["classification"],
        "status": "PASS",
        "trace_sha256": row["trace_sha256"],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-gate", type=Path, required=True)
    ap.add_argument("--contract", type=Path, required=True)
    ap.add_argument("--ws20", type=Path, required=True)
    ap.add_argument("--ws21", type=Path, required=True)
    ap.add_argument("--ws22", type=Path, required=True)
    ap.add_argument("--ws23", type=Path, required=True)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    contract = load(args.contract)
    base = load(args.base_gate)
    ws20_gate_path = find_one(args.ws20, "WS20_GATE.json")
    ws21_gate_path = find_one(args.ws21, "WS21_ENGINE_TRANSPORT_GATE.json")
    ws22_gate_path = find_one(args.ws22, "WS22_FAILURE_REPLAY_HIDDEN_GATE.json")
    ws23_gate_path = find_one(args.ws23, "WS23_GATE.json")
    ws20 = load(ws20_gate_path)
    ws21 = load(ws21_gate_path)
    ws22 = load(ws22_gate_path)
    ws23 = load(ws23_gate_path)

    assert contract["$id"] == "commander-simulator-next.failure-outcome.v1"
    assert contract["properties"]["category"]["enum"] == CATEGORIES
    assert len(base["category_matrix"]) == 16
    assert set(r["outcome"]["category"] for r in base["category_matrix"]) == set(CATEGORIES)
    assert all(contract["x-categories"][c]["production_reachable"] is True for c in CATEGORIES)

    assert ws20["status"] == "PASS" and ws20["WORKSTREAM_COMPLETE"] is True
    assert all(ws20["hard_gate"].values())
    assert ws21["status"] == "PASS" and ws21["ENGINE_FAILURE"] == "PASS" and ws21["TRANSPORT_FAILURE"] == "PASS"
    assert all(ws21["hard_gates"].values())
    assert ws22["status"] == "PASS" and ws22["REPLAY_DIVERGENCE"] == "PASS" and ws22["HIDDEN_INFO_VIOLATION"] == "PASS"
    assert all(ws22["hard_gates"].values())
    assert ws22["regression_implications"]["Q2_PRINCIPAL_HIDDEN_INFORMATION"]["decision"] == "NO_RERUN"
    assert ws22["regression_implications"]["Q3_SEMANTIC_REPLAY"]["decision"] == "NO_RERUN"
    assert ws23["status"] == "PASS" and ws23["WORKSTREAM_COMPLETE"] is True
    assert ws23["classification"] == "CARD_BEHAVIOR_FAILURE"
    assert ws23["production_binding"] == "QUALIFIER_ONLY" and ws23["production_reachable"] is False
    assert all(ws23["hard_gates"].values())

    matrix: dict[str, dict[str, Any]] = {}
    for category in RETAINED_WS12:
        matrix[category] = retained_row(base, contract, category)

    for category in ("ACTION_NOT_COMPLETABLE", "UNSUPPORTED_RULES_PATH"):
        src = ws20["categories"][category]
        trace_name = f"{category}_TRACE.json"
        trace_path = find_one(args.ws20, trace_name)
        matrix[category] = {
            "category": category,
            "contract_production_reachable": True,
            "production_reachable": True,
            "reachable_boundary": src["actual_boundary"],
            "detector_adapter": "WS20 exact production guard",
            "typed_result": category,
            "state_commit_semantics": "FORBIDDEN",
            "observed_state_committed": False,
            "hidden_info_safe": src["public_payload_hidden_info_marker_count"] == 0,
            "fallback_absent": src["no_fallback_coercion"] is True,
            "evidence_source": "WS20",
            "evidence_class": src["evidence_class"],
            "classification": src["classification"],
            "status": "PASS",
            "trace_sha256": sha256(trace_path),
        }

    for category in ("ENGINE_FAILURE", "TRANSPORT_FAILURE"):
        trace_path, trace = find_ws21_trace(args.ws21, category)
        matrix[category] = {
            "category": category,
            "contract_production_reachable": True,
            "production_reachable": True,
            "reachable_boundary": "GameAction.changeZone engine entry" if category == "ENGINE_FAILURE" else "WS01 external-decision transport decode boundary",
            "detector_adapter": "WS21 actual-path engine/transport adapter",
            "typed_result": trace["category"],
            "state_commit_semantics": "FORBIDDEN",
            "observed_state_committed": trace["state_committed"],
            "hidden_info_safe": True,
            "fallback_absent": True,
            "evidence_source": "WS21",
            "evidence_class": "TECHNICALLY_CONFORMANT",
            "classification": "PASS",
            "status": "PASS",
            "trace_sha256": sha256(trace_path),
        }

    for category in ("REPLAY_DIVERGENCE", "HIDDEN_INFO_VIOLATION"):
        src = ws22["categories"][category]
        matrix[category] = {
            "category": category,
            "contract_production_reachable": True,
            "production_reachable": True,
            "reachable_boundary": src["production_binding"],
            "detector_adapter": src["production_binding"],
            "typed_result": category,
            "state_commit_semantics": "FORBIDDEN",
            "observed_state_committed": False,
            "hidden_info_safe": True,
            "fallback_absent": True,
            "evidence_source": "WS22",
            "evidence_class": src["evidence_class"],
            "classification": "PASS",
            "status": "PASS",
            "trace_sha256": src["trace_sha256"],
        }

    # WS23 proves the semantic verifier itself, but the authoritative WS12 contract
    # still defines CARD_BEHAVIOR_FAILURE as production reachable.  No audited
    # production callsite binds that verifier, so the production row must remain
    # untyped/fail-closed.  Do not rewrite contract reachability to get a green gate.
    matrix["CARD_BEHAVIOR_FAILURE"] = {
        "category": "CARD_BEHAVIOR_FAILURE",
        "contract_production_reachable": True,
        "production_reachable": True,
        "reachable_boundary": "UNBOUND_PRODUCTION_CARD_BEHAVIOR_VERIFIER",
        "detector_adapter": "WS23 QUALIFIER_ONLY semantic verifier",
        "typed_result": "CARD_BEHAVIOR_FAILURE_IN_QUALIFIER_ONLY",
        "state_commit_semantics": "FORBIDDEN",
        "observed_state_committed": False,
        "hidden_info_safe": ws23["hard_gates"]["public_payload_semantic_values_absent"] is True,
        "fallback_absent": None,
        "evidence_source": "WS23",
        "evidence_class": "UNKNOWN_FOR_PRODUCTION_BINDING",
        "qualifier_evidence_class": ws23["evidence_class"],
        "classification": "PARTIAL",
        "status": "FAIL_CLOSED",
        "trace_sha256": ws23["baseline"]["trace_sha256"],
        "blocker": "WS12 contract says production_reachable=true, but WS23 proves only a QUALIFIER_ONLY detector and no production runtime callsite.",
    }

    ordered = [matrix[c] for c in CATEGORIES]
    assert len(ordered) == 16
    assert all(r["typed_result"] == r["category"] for r in ordered if r["category"] != "CARD_BEHAVIOR_FAILURE")
    assert all(r["hidden_info_safe"] is True for r in ordered)
    assert all(r["observed_state_committed"] is False for r in ordered if r["category"] != "SUCCESS")

    untyped = [r["category"] for r in ordered if r["production_reachable"] and r["status"] != "PASS"]
    unknown_fallback = [r["category"] for r in ordered if r["production_reachable"] and r["fallback_absent"] is None]
    observed_fallback = [r["category"] for r in ordered if r["fallback_absent"] is False]
    assert untyped == ["CARD_BEHAVIOR_FAILURE"]
    assert unknown_fallback == ["CARD_BEHAVIOR_FAILURE"]
    assert observed_fallback == []

    trace_inventory = [
        {"category": r["category"], "source": r["evidence_source"], "trace_sha256": r["trace_sha256"], "classification": r["classification"]}
        for r in ordered
    ]
    gate = {
        "schema": "commander-simulator-next.failure-semantics-gate.v2",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "base_sha": "80743bdbc2950b00e422f3deb38f04111f30a4d4",
        "forge_pin": FORGE_PIN,
        "category_count": 16,
        "category_matrix": ordered,
        "production_reachable_untyped_failure_outcomes": len(untyped),
        "production_reachable_untyped_categories": untyped,
        "production_reachable_fallback_observed_count": len(observed_fallback),
        "production_reachable_fallback_failure_handling": "UNKNOWN" if unknown_fallback else len(observed_fallback),
        "production_reachable_fallback_unknown_categories": unknown_fallback,
        "Q2_PRINCIPAL_HIDDEN_INFORMATION": "NO_RERUN",
        "Q3_SEMANTIC_REPLAY": "NO_RERUN",
        "hard_gates": {
            "ALL_16_CATEGORIES_ACCOUNTED_FOR": len(ordered) == 16,
            "SIX_SUCCESSOR_PRODUCTION_BINDINGS_PASS": all(matrix[c]["status"] == "PASS" for c in ["ACTION_NOT_COMPLETABLE", "UNSUPPORTED_RULES_PATH", "ENGINE_FAILURE", "TRANSPORT_FAILURE", "REPLAY_DIVERGENCE", "HIDDEN_INFO_VIOLATION"]),
            "RETAINED_WS12_TYPED_PATHS_PRESERVED": all(matrix[c]["status"] == "PASS" for c in RETAINED_WS12),
            "CARD_BEHAVIOR_QUALIFIER_DETECTOR_PASS": ws23["status"] == "PASS",
            "CARD_BEHAVIOR_PRODUCTION_BINDING_CLOSED": False,
            "REACHABLE_UNTYPED_FAILURES_ZERO": len(untyped) == 0,
            "REACHABLE_FALLBACK_HANDLING_ZERO_PROVEN": not unknown_fallback and not observed_fallback,
            "OBSERVED_PROHIBITED_FALLBACKS_ZERO": len(observed_fallback) == 0,
            "HIDDEN_INFO_SAFE_PAYLOADS": all(r["hidden_info_safe"] is True for r in ordered),
            "FAILED_STATE_COMMITS_ZERO": all(r["observed_state_committed"] is False for r in ordered if r["category"] != "SUCCESS"),
            "Q2_Q3_NO_RERUN_PRESERVED": True,
        },
        "blockers": [{
            "category": "CARD_BEHAVIOR_FAILURE",
            "evidence_class": "UNKNOWN",
            "required_evidence": "Bind a real production runtime card-behavior semantic verifier/capture path, induce an actual semantic mismatch at that path, emit CARD_BEHAVIOR_FAILURE, and prove no state commit/fallback/private-data disclosure.",
        }],
        "FAILURE_SEMANTICS": "FAIL_CLOSED",
        "WORKSTREAM_COMPLETE": True,
        "evidence_class": "UNKNOWN",
        "architecture_freeze": "NOT_AUTHORIZED_BY_THIS_WORKSTREAM",
    }

    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    matrix_doc = {"schema": "commander-simulator-next.failure-semantics-matrix.v2", "categories": ordered}
    trace_doc = {"schema": "commander-simulator-next.failure-semantics-trace-inventory.v2", "traces": trace_inventory}
    (out / "FAILURE_SEMANTICS_GATE.v2.json").write_bytes(canonical(gate))
    (out / "FAILURE_SEMANTICS_MATRIX.v2.json").write_bytes(canonical(matrix_doc))
    (out / "FAILURE_SEMANTICS_TRACE_INVENTORY.v2.json").write_bytes(canonical(trace_doc))
    md = [
        "# Failure Semantics Gate v2", "", f"- Workstream complete: **TRUE**",
        f"- FAILURE_SEMANTICS: **{gate['FAILURE_SEMANTICS']}**",
        f"- Categories: **16/16**", f"- Production-reachable untyped categories: **{len(untyped)}** (`{', '.join(untyped)}`)",
        f"- Observed prohibited fallback handlers: **{len(observed_fallback)}**",
        f"- Fallback absence for production CARD_BEHAVIOR_FAILURE: **UNKNOWN**",
        "- Q2: **NO_RERUN**", "- Q3: **NO_RERUN**", "",
        "The sole blocker is the missing production binding for CARD_BEHAVIOR_FAILURE. WS23's verifier is qualification-only; the WS12 authoritative contract still marks the category production-reachable. No runtime adapter was invented.", "",
        "`ARCHITECTURE_FREEZE = NOT AUTHORIZED BY THIS WORKSTREAM`", "",
    ]
    (out / "FAILURE_SEMANTICS_GATE.v2.md").write_text("\n".join(md), encoding="utf-8")
    names = ["FAILURE_SEMANTICS_GATE.v2.json", "FAILURE_SEMANTICS_GATE.v2.md", "FAILURE_SEMANTICS_MATRIX.v2.json", "FAILURE_SEMANTICS_TRACE_INVENTORY.v2.json"]
    (out / "WS25_HASHES.sha256").write_text("\n".join(f"{sha256(out / n)}  {n}" for n in names) + "\n", encoding="utf-8")
    print("WS25_CATEGORY_COUNT=16")
    print("WS25_PRODUCTION_REACHABLE_UNTYPED=1")
    print("WS25_CARD_BEHAVIOR_PRODUCTION_BINDING=UNKNOWN")
    print("FAILURE_SEMANTICS=FAIL_CLOSED")
    print("WORKSTREAM_COMPLETE=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
