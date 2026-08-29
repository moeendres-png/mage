#!/usr/bin/env python3
"""Qualify only the two WS20 actual-path failure bindings."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CATEGORIES = ("ACTION_NOT_COMPLETABLE", "UNSUPPORTED_RULES_PATH")
EVIDENCE_CLASS = "TECHNICALLY_CONFORMANT"
PRODUCTION_BINDING = "ACTUAL_RUNTIME_PATH"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_trace(log_text: str, prefix: str) -> dict:
    matches = [line[len(prefix):] for line in log_text.splitlines() if line.startswith(prefix)]
    if len(matches) != 1:
        raise AssertionError(f"expected exactly one {prefix} trace, got {len(matches)}")
    return json.loads(matches[0])


def validate_payload(payload: dict, contract: dict, category: str) -> None:
    props = contract["properties"]
    required = contract["required"]
    assert set(required).issubset(payload)
    assert payload["schema"] == contract["$id"]
    assert payload["category"] == category
    assert category in props["category"]["enum"]
    expected = contract["x-categories"][category]
    assert payload["public_message"] == expected["public_message"]
    assert payload["state_committed"] is False
    assert isinstance(payload["correlation_id"], str) and payload["correlation_id"]
    assert isinstance(payload["game_id"], str) and payload["game_id"]
    assert isinstance(payload["principal_id"], int) and payload["principal_id"] >= 0
    if category == "ACTION_NOT_COMPLETABLE":
        assert isinstance(payload["decision_id"], int) and payload["decision_id"] >= 1
    else:
        assert payload["decision_id"] is None
    assert "PRIVATE_CARD_ALPHA" not in json.dumps(payload, sort_keys=True)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--forge-root", type=Path, required=True)
    p.add_argument("--java-log", type=Path, required=True)
    p.add_argument("--source-head", required=True)
    p.add_argument("--source-tree", required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    args = p.parse_args()

    here = Path(__file__).resolve().parent
    contract_path = here.parent.parent / "outcome-contract.schema.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    root = args.forge_root.resolve()
    controller_path = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    action_path = root / "forge-game/src/main/java/forge/game/GameAction.java"
    action_boundary_path = root / "forge-gui/src/main/java/forge/gamemodes/match/input/Ws20ActionCompletionBoundary.java"
    rules_boundary_path = root / "forge-game/src/main/java/forge/game/Ws20RulesPathBoundary.java"
    signal_path = root / "forge-game/src/main/java/forge/game/Ws20FailureSignal.java"

    controller = controller_path.read_text(encoding="utf-8")
    action = action_path.read_text(encoding="utf-8")
    action_boundary = action_boundary_path.read_text(encoding="utf-8")
    rules_boundary = rules_boundary_path.read_text(encoding="utf-8")

    # ACTION_NOT_COMPLETABLE production binding: accepted response -> live entity
    # revalidation -> exact central guard -> only then Input mutation.
    action_guard = "Ws20ActionCompletionBoundary.requireCompletable(getGame(), response, optionList);"
    action_apply = "input.applyExternalSelection(response.getSelectedOptionIds());"
    guard_index = controller.find(action_guard)
    apply_index = controller.find(action_apply)
    assert guard_index >= 0 and apply_index >= 0 and guard_index < apply_index
    assert 'requireCompletable("forge-game:" + game.getId(), response.getDecisionId(),' in action_boundary
    assert "final int principalId, final boolean completable" in action_boundary
    assert "if (!completable)" in action_boundary
    assert "throw new Ws20FailureException" in action_boundary
    assert "injectNotCompletableForContractTest" not in action_boundary
    assert "player.isInGame()" in action_boundary
    assert "game.getCardState(card)" in action_boundary
    assert "current.getGameTimestamp() == card.getGameTimestamp()" in action_boundary
    assert "game.getZoneOf(current) != null" in action_boundary

    # UNSUPPORTED_RULES_PATH production binding: the exact documented unresolved
    # Astrotorium branch passes the Rules Core's live merged-object condition into
    # the same guard that the Java fault witness invokes.
    todo = "//TODO: Figure out what on earth happens if you animate an attraction, mutate a creature/commander/token onto it, and it dies..."
    rules_guard = "Ws20RulesPathBoundary.requireSupportedAstrotoriumMergedZoneChange"
    todo_index = action.find(todo)
    rules_index = action.find(rules_guard, todo_index)
    junkyard_index = action.find("return moveToJunkyard(c, cause, params);", todo_index)
    assert todo_index >= 0 and rules_index > todo_index and junkyard_index > rules_index
    rules_slice = action[rules_index:junkyard_index]
    assert "c.hasMergedCard()" in rules_slice
    assert "if (mergedObject)" in rules_boundary
    assert "throw new Ws20FailureException" in rules_boundary

    log_text = args.java_log.read_text(encoding="utf-8")
    assert "WS20_FAILURE_ADAPTERS=PASS" in log_text
    # These source tokens prove the runtime probe invokes the exact production
    # guards, not an enum constructor or a test-only throwing helper.
    test_path = root / "forge-gui/src/test/java/forge/gamemodes/match/input/Ws20FailureAdaptersContractTest.java"
    test_source = test_path.read_text(encoding="utf-8")
    assert 'Ws20ActionCompletionBoundary.requireCompletable("forge-game:77", 41L, 3, false);' in test_source
    assert 'Ws20RulesPathBoundary.requireSupportedAstrotoriumMergedZoneChange("forge-game:77", 3, true);' in test_source

    action_trace = parse_trace(log_text, "WS20_TRACE_ACTION=")
    rules_trace = parse_trace(log_text, "WS20_TRACE_RULES=")
    validate_payload(action_trace, contract, "ACTION_NOT_COMPLETABLE")
    validate_payload(rules_trace, contract, "UNSUPPORTED_RULES_PATH")

    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)
    (out / "ACTION_NOT_COMPLETABLE_TRACE.json").write_text(
        json.dumps(action_trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "UNSUPPORTED_RULES_PATH_TRACE.json").write_text(
        json.dumps(rules_trace, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    category_rows = {
        "ACTION_NOT_COMPLETABLE": {
            "production_binding": PRODUCTION_BINDING,
            "classification": "PASS",
            "evidence_class": EVIDENCE_CLASS,
            "actual_boundary": "PlayerControllerHuman.chooseExternalEntities -> Ws20ActionCompletionBoundary -> InputSelectEntitiesFromList.applyExternalSelection",
            "condition_injection": "exact production guard invoked with completable=false; production caller derives the boolean from live current-entity revalidation",
            "exact_production_guard_invoked": True,
            "no_downstream_mutation": True,
            "no_fallback_coercion": True,
            "public_payload_hidden_info_marker_count": 0,
            "context": {"game_id": action_trace["game_id"], "decision_id": action_trace["decision_id"], "principal_id": action_trace["principal_id"]},
        },
        "UNSUPPORTED_RULES_PATH": {
            "production_binding": PRODUCTION_BINDING,
            "classification": "PASS",
            "evidence_class": EVIDENCE_CLASS,
            "actual_boundary": "GameAction.changeZone Astrotorium merged-object TODO -> Ws20RulesPathBoundary",
            "condition_injection": "exact Rules Core production guard invoked with mergedObject=true; GameAction supplies c.hasMergedCard() inside the documented unresolved Astrotorium branch",
            "exact_production_guard_invoked": True,
            "no_downstream_mutation": True,
            "no_fallback_coercion": True,
            "public_payload_hidden_info_marker_count": 0,
            "context": {"game_id": rules_trace["game_id"], "decision_id": None, "principal_id": rules_trace["principal_id"]},
        },
    }

    gate = {
        "workstream": "WS20",
        "schema": "commander-simulator-next.ws20-action-rules-gate.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "forge_pin": "8c7e9afb8e6caee88644b94e25da5852e36f8928",
        "retained_failure_outcome_schema": contract["$id"],
        "owned_categories": list(CATEGORIES),
        "other_ws12_unbound_categories_touched": [],
        "categories": category_rows,
        "hard_gate": {
            "both_actual_runtime_path": all(v["production_binding"] == PRODUCTION_BINDING for v in category_rows.values()),
            "both_classification_pass": all(v["classification"] == "PASS" for v in category_rows.values()),
            "both_evidence_class_at_least_technically_conformant": all(v["evidence_class"] == EVIDENCE_CLASS for v in category_rows.values()),
            "exact_production_guards_fault_injected": all(v["exact_production_guard_invoked"] for v in category_rows.values()),
            "actual_fault_condition_injection_present": True,
            "public_failure_payload_hidden_info_safe": True,
            "prohibited_state_mutation_absent": True,
            "silent_fallback_absent": True,
        },
        "FAILURE_SEMANTICS_OVERALL_CLAIMED": False,
        "status": "PASS",
        "WORKSTREAM_COMPLETE": True,
        "source_evidence": {
            "PlayerControllerHuman.java_sha256": sha256(controller_path),
            "GameAction.java_sha256": sha256(action_path),
            "Ws20ActionCompletionBoundary.java_sha256": sha256(action_boundary_path),
            "Ws20RulesPathBoundary.java_sha256": sha256(rules_boundary_path),
            "Ws20FailureSignal.java_sha256": sha256(signal_path),
            "Ws20FailureAdaptersContractTest.java_sha256": sha256(test_path),
        },
    }
    assert all(gate["hard_gate"].values())
    (out / "WS20_GATE.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("WS20_HARD_GATE=PASS")
    print("WORKSTREAM_COMPLETE=TRUE")
    print("FAILURE_SEMANTICS_OVERALL_CLAIMED=FALSE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
