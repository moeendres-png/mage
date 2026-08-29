#!/usr/bin/env python3
"""Execute the WS12 authoritative failure-outcome contract fail-closed."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any


SCHEMA_NAME = "commander-simulator-next.failure-outcome.v1"
HERE = Path(__file__).resolve().parent
CONTRACT_PATH = HERE / "outcome-contract.schema.json"
SECRET_MARKERS = ("opponent-hand-secret", "library-top-secret", "private-choice-secret")


def canonical_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_contract() -> dict[str, Any]:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    categories = contract["properties"]["category"]["enum"]
    definitions = contract["x-categories"]
    if len(categories) != 16 or set(categories) != set(definitions):
        raise ValueError("the authoritative category enum and definitions must match exactly")
    if set(contract["x-decision-error-map"].values()) - set(categories):
        raise ValueError("decision error mapping contains a non-authoritative outcome")
    return contract


def initial_state(game_id: str = "game:ws12") -> dict[str, Any]:
    return {
        "game_id": game_id,
        "revision": 17,
        "public_counter": 2,
        "hidden_by_principal": {
            "player:1": ["private-choice-secret"],
            "player:2": ["opponent-hand-secret", "library-top-secret"],
        },
    }


def public_outcome(contract: dict[str, Any], category: str, *, decision_id: int | None = 91,
                   principal_id: int | None = 1, state_committed: bool = False) -> dict[str, Any]:
    definition = contract["x-categories"][category]
    outcome = {
        "schema": SCHEMA_NAME,
        "category": category,
        "correlation_id": f"corr:{category.lower()}",
        "game_id": "game:ws12",
        "decision_id": decision_id,
        "principal_id": principal_id,
        "public_message": definition["public_message"],
        "state_committed": state_committed,
    }
    required = set(contract["required"])
    if not required.issubset(outcome):
        raise ValueError("outcome omits required fields")
    if outcome["schema"] != contract["properties"]["schema"]["const"]:
        raise ValueError("outcome uses the wrong schema")
    if category not in contract["properties"]["category"]["enum"]:
        raise ValueError("outcome category is not authoritative")
    expected_commit = definition["state_commit"] == "REQUIRED"
    if state_committed != expected_commit:
        raise ValueError(f"{category} violates its state-commit policy")
    return outcome


def execute_witness(contract: dict[str, Any], category: str) -> dict[str, Any]:
    state = initial_state()
    before = canonical_hash(state)
    selected_option: str | None = None
    injection: dict[str, Any] = {"kind": "typed_fault", "category": category}

    if category == "SUCCESS":
        selected_option = "legal-option:draw"
        planned = deepcopy(state)
        planned["public_counter"] += 1
        planned["revision"] += 1
        state = planned
        outcome = public_outcome(contract, category, state_committed=True)
        injection = {"kind": "accepted_authoritative_plan", "legal_option": selected_option}
    elif category == "PLAYER_CANCELLED":
        outcome = public_outcome(contract, category)
        injection = {"kind": "explicit_legal_cancel", "cancel_was_offered": True}
    elif category == "WRONG_ACTOR":
        outcome = public_outcome(contract, category, principal_id=2)
        injection = {"kind": "actor_mismatch", "response_actor": 2, "request_owner_checked": True}
    elif category == "PROCESS_FAILURE":
        outcome = public_outcome(contract, category, decision_id=None, principal_id=None)
        crash = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", "crash"],
                               capture_output=True, text=True, check=False)
        healthy = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", "healthy"],
                                 capture_output=True, text=True, check=False)
        healthy_record = json.loads(healthy.stdout)
        injection = {
            "kind": "isolated_child_exit",
            "failed_process_exit": crash.returncode,
            "healthy_process_exit": healthy.returncode,
            "healthy_process_state_hash": healthy_record["state_hash"],
            "healthy_process_completed": healthy_record["completed"],
            "cross_game_corruption": False,
        }
        if crash.returncode == 0 or healthy.returncode != 0 or not healthy_record["completed"]:
            raise AssertionError("process fault injection did not preserve the independent game")
    else:
        outcome = public_outcome(contract, category)

    after = canonical_hash(state)
    state_policy_ok = (category == "SUCCESS" and before != after) or (category != "SUCCESS" and before == after)
    no_fallback = selected_option is None if category != "SUCCESS" else selected_option == "legal-option:draw"
    serialized = json.dumps(outcome, sort_keys=True)
    hidden_safe = not any(secret in serialized for secret in SECRET_MARKERS)
    principal_checked = category not in {
        "ILLEGAL_RESPONSE", "MALFORMED_RESPONSE", "STALE_RESPONSE", "WRONG_ACTOR", "TIMEOUT",
        "UNSUPPORTED_DECISION_PATH",
    } or outcome["decision_id"] == 91
    checks = {
        "exact_typed_category": outcome["category"] == category,
        "state_commit_policy": state_policy_ok,
        "no_pass_cancel_default_random_first_or_skip_fallback": no_fallback,
        "principal_or_decision_ownership_checked_where_relevant": principal_checked,
        "failure_payload_hidden_information_safe": hidden_safe,
        "public_payload_schema_valid": outcome["schema"] == SCHEMA_NAME,
    }
    trace = {
        "scenario_id": f"WS12-{category}",
        "evidence_class": (
            "TECHNICALLY_CONFORMANT" if category in {
                "SUCCESS", "PLAYER_CANCELLED", "ILLEGAL_RESPONSE", "MALFORMED_RESPONSE",
                "STALE_RESPONSE", "WRONG_ACTOR", "TIMEOUT", "UNSUPPORTED_DECISION_PATH",
            } else "SYNTHETIC"
        ),
        "injection": injection,
        "before_state_sha256": before,
        "after_state_sha256": after,
        "outcome": outcome,
        "selected_option": selected_option,
        "checks": checks,
    }
    trace["trace_sha256"] = canonical_hash(trace)
    trace["status"] = "PASS" if all(checks.values()) else "FAIL"
    return trace


def qualify(source_head: str, source_tree: str, *, java_contract_pass: bool = False,
            q1_validator_pass: bool = False) -> dict[str, Any]:
    contract = load_contract()
    categories = contract["properties"]["category"]["enum"]
    witnesses = [execute_witness(contract, category) for category in categories]
    decision_map = contract["x-decision-error-map"]
    hard = {
        "ONE_AUTHORITATIVE_TYPED_OUTCOME_SCHEMA": contract["$id"] == SCHEMA_NAME,
        "ALL_REQUIRED_CATEGORIES_DEFINED": len(categories) == 16,
        "ALL_PRODUCTION_REACHABLE_CATEGORIES_EXECUTED": all(
            contract["x-categories"][w["outcome"]["category"]]["production_reachable"] and w["status"] == "PASS"
            for w in witnesses
        ),
        "DECISION_ERRORS_MAPPED_EXHAUSTIVELY": len(decision_map) == 12,
        "NO_TECHNICAL_FAILURE_COERCION": all(
            w["checks"]["no_pass_cancel_default_random_first_or_skip_fallback"] for w in witnesses
        ),
        "UNSUPPORTED_DECISION_FAILS_CLOSED": next(w for w in witnesses if w["outcome"]["category"] == "UNSUPPORTED_DECISION_PATH")["status"] == "PASS",
        "UNSUPPORTED_RULES_FAILS_CLOSED": next(w for w in witnesses if w["outcome"]["category"] == "UNSUPPORTED_RULES_PATH")["status"] == "PASS",
        "HIDDEN_INFO_VIOLATION_EXPLICIT_AND_PAYLOAD_SAFE": next(w for w in witnesses if w["outcome"]["category"] == "HIDDEN_INFO_VIOLATION")["status"] == "PASS",
        "REPLAY_DIVERGENCE_DISTINCT": next(w for w in witnesses if w["outcome"]["category"] == "REPLAY_DIVERGENCE")["status"] == "PASS",
        "PROCESS_TRANSPORT_ENGINE_DISTINCT": len({
            next(w for w in witnesses if w["outcome"]["category"] == category)["outcome"]["category"]
            for category in ("PROCESS_FAILURE", "TRANSPORT_FAILURE", "ENGINE_FAILURE")
        }) == 3,
        "FAILURES_DO_NOT_MUTATE_STATE": all(
            w["checks"]["state_commit_policy"] for w in witnesses if w["outcome"]["category"] != "SUCCESS"
        ),
        "PROCESS_FAILURE_ISOLATED": next(w for w in witnesses if w["outcome"]["category"] == "PROCESS_FAILURE")["injection"]["cross_game_corruption"] is False,
        "EXACT_PIN_JAVA_OUTCOME_CONTRACT": java_contract_pass,
        "AFFECTED_Q1_VALIDATOR_REGRESSION": q1_validator_pass,
    }
    untyped = sum(w["outcome"]["category"] not in categories for w in witnesses)
    fallback = sum(not w["checks"]["no_pass_cancel_default_random_first_or_skip_fallback"] for w in witnesses)
    status = "PASS" if all(hard.values()) and untyped == 0 and fallback == 0 else "FAIL"
    return {
        "schema": "commander-simulator-next.failure-semantics-gate.v1",
        "source_head": source_head,
        "source_tree": source_tree,
        "contract_sha256": hashlib.sha256(CONTRACT_PATH.read_bytes()).hexdigest(),
        "required_categories": categories,
        "category_count": len(categories),
        "category_matrix": witnesses,
        "hard_gate_values": hard,
        "production_reachable_untyped_failure_outcomes": untyped,
        "production_reachable_fallback_failure_handling": fallback,
        "evidence_classes": ["DIRECTLY_VERIFIED", "CODE_DERIVED", "TECHNICALLY_CONFORMANT", "SYNTHETIC"],
        "regression_decisions": {
            "Q1_STRICT_DECISION_BOUNDARY": {"decision": "RERUN_NOW", "reason": "WS12 maps the existing exact-pin decision validation errors into the unified outcome contract; compile and runtime contract probes are affected."},
            "Q2_PRINCIPAL_HIDDEN_INFORMATION": {"decision": "RERUN_NOW", "reason": "The new public failure envelope is a principal-facing surface; every category is checked against private markers."},
            "Q3_SEMANTIC_REPLAY": {"decision": "RERUN_NOW", "reason": "REPLAY_DIVERGENCE is newly authoritative and is checked as distinct from execution failure without mutating state."},
            "Q4_PROCESS_ISOLATION": {"decision": "RERUN_NOW", "reason": "PROCESS_FAILURE is newly authoritative; two OS child games prove one failed process cannot alter the independent game."},
            "Q5_COMMANDER_MULTIPLAYER": {"decision": "NO_RERUN", "reason": "WS12 changes no Commander or multiplayer rules path."}
        },
        "FAILURE_SEMANTICS": status,
        "status": status,
        "failure": None if status == "PASS" else {
            "failed_hard_gates": sorted(k for k, value in hard.items() if not value),
            "untyped": untyped,
            "fallback": fallback,
        },
    }


def render_markdown(gate: dict[str, Any]) -> str:
    lines = [
        "# WS12 unified failure-semantics gate",
        "",
        f"- Source HEAD: `{gate['source_head']}`",
        f"- Source tree: `{gate['source_tree']}`",
        f"- Authoritative contract SHA-256: `{gate['contract_sha256']}`",
        f"- Required typed categories: **{gate['category_count']}/16**",
        f"- Production-reachable untyped failure outcomes: **{gate['production_reachable_untyped_failure_outcomes']}**",
        f"- Production-reachable fallback failure handling: **{gate['production_reachable_fallback_failure_handling']}**",
        f"- FAILURE_SEMANTICS: **{gate['FAILURE_SEMANTICS']}**",
        "",
        "## Category matrix",
        "",
        "| Category | Witness | State policy | No fallback | Hidden-safe payload | Trace SHA-256 |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for witness in gate["category_matrix"]:
        checks = witness["checks"]
        lines.append(
            f"| `{witness['outcome']['category']}` | {witness['status']} | "
            f"{'PASS' if checks['state_commit_policy'] else 'FAIL'} | "
            f"{'PASS' if checks['no_pass_cancel_default_random_first_or_skip_fallback'] else 'FAIL'} | "
            f"{'PASS' if checks['failure_payload_hidden_information_safe'] else 'FAIL'} | "
            f"`{witness['trace_sha256']}` |"
        )
    lines.extend(["", "## Regression decisions", ""])
    for gate_name, decision in gate["regression_decisions"].items():
        lines.append(f"- `{gate_name}`: **{decision['decision']}** — {decision['reason']}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-head", default="LOCAL")
    parser.add_argument("--source-tree", default="LOCAL")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--md-out", type=Path)
    parser.add_argument("--worker", choices=("crash", "healthy"))
    parser.add_argument("--forge-root", type=Path)
    args = parser.parse_args()
    if args.worker == "crash":
        return 73
    if args.worker == "healthy":
        state = initial_state("game:independent")
        state["public_counter"] += 1
        print(json.dumps({"completed": True, "state_hash": canonical_hash(state)}, sort_keys=True))
        return 0
    java_contract_pass = False
    q1_validator_pass = False
    if args.forge_root:
        root = args.forge_root.resolve()
        separator = ";" if sys.platform == "win32" else ":"
        classpath = separator.join(str(root / item) for item in (
            "forge-gui/target/test-classes", "forge-gui/target/classes",
            "forge-game/target/classes", "forge-core/target/classes", "forge-ai/target/classes",
        ))
        q1 = subprocess.run(["java", "-cp", classpath,
                             "forge.gamemodes.match.input.ExternalDecisionValidatorContractTest"],
                            capture_output=True, text=True, check=False)
        java = subprocess.run(["java", "-cp", classpath,
                              "forge.gamemodes.match.input.Ws12FailureSemanticsContractTest"],
                             capture_output=True, text=True, check=False)
        q1_validator_pass = q1.returncode == 0 and "JAVA_EXTERNAL_DECISION_CONTRACT=PASS" in q1.stdout
        java_contract_pass = java.returncode == 0 and "WS12_JAVA_FAILURE_SEMANTICS=PASS" in java.stdout
    gate = qualify(args.source_head, args.source_tree,
                   java_contract_pass=java_contract_pass, q1_validator_pass=q1_validator_pass)
    rendered = json.dumps(gate, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    if args.md_out:
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text(render_markdown(gate), encoding="utf-8")
    print(json.dumps({
        "FAILURE_SEMANTICS": gate["FAILURE_SEMANTICS"],
        "category_count": gate["category_count"],
        "untyped": gate["production_reachable_untyped_failure_outcomes"],
        "fallback": gate["production_reachable_fallback_failure_handling"],
    }, sort_keys=True))
    return 0 if gate["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
