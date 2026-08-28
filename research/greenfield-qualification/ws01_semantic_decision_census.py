#!/usr/bin/env python3
"""Fail-closed semantic 109/15 census for the WS01 strict external-pilot boundary.

The old `109 - 3` metric was only a syntactic baseline. This closeout census
classifies every exact PlayerController callback by semantics, requires an
explicit externalization route for every production-reachable discretionary
callback, separately classifies all 15 blocking GUI return paths, and validates
the real 4P Commander Decision Tape. UNKNOWN is always a hard failure.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


NONDECISION_CONTROLLER = {
    "playSpellAbilityNoStack",
    "playTrigger",
    "playSaFromPlayEffect",
    "reveal",
    "notifyOfValue",
    "playChosenSpellAbility",
    "getCostDecisionMaker",
    "revealAISkipCards",
    "revealUnsupported",
    "autoPassCancel",
    "awaitNextInput",
    "cancelAwaitNextInput",
}

# Production boundary for WS01 is one rules-resolved Commander game. Between-
# game sideboarding and ante deck mutation are not reachable in that production
# mode. They remain fail-closed rather than being silently defaulted.
NONPRODUCTION_COMMANDER_CONTROLLER = {
    "sideboard",
    "chooseCardsYouWonToAddToDeck",
    "revealAnte",
}

# These callbacks do not contain a directly detected chooseExternal* call but
# delegate to a previously classified typed callback or to an explicitly driven
# Forge input state machine. The exact patched source markers below are also
# required before these routes are accepted.
EXPLICIT_DELEGATED_OR_STATE_MACHINE = {
    "orderAndPlaySimultaneousSa",
    "choosePermanentsToSacrifice",
    "choosePermanentsToDestroy",
    "chooseNewTargetsFor",
    "helpPayForAssistSpell",
    "chooseCardsToDiscardUnlessType",
    "chooseCardsForConvokeOrImprovise",
    "chooseNumberForCostReduction",
    "chooseColor",
    "chooseColorAllowColorless",
    "payCostToPreventEffect",
    "payCostDuringRoll",
    "payCombatCost",
    "payManaCost",
    "applyManaToCost",
    "chooseCardsForCost",
    "chooseCardName",
    "assignCombatDamage",
    "orderBlockers",
    "orderBlocker",
    "orderAttackers",
    "orderMoveToZoneList",
    "orderCosts",
}

GUI_PRESENTATION_NONDECISION = {"tempShowZones", "openZones"}
GUI_NONPRODUCTION_COMMANDER = {"sideboard"}
GUI_TYPED_CONTROLLER_BYPASS = {"getAbilityToPlay", "assignCombatDamage", "assignGenericAmount"}
GUI_STRICT_UNREACHABLE_HELPER = {"manipulateCardList"}
GUI_TYPED_ADAPTER = {
    "showConfirmDialog", "showOptionDialog", "showInputDialog", "confirm",
    "getChoices", "order", "chooseSingleEntityForEffect", "chooseEntitiesForEffect",
}


def controller_route(item: dict) -> tuple[str, bool]:
    name = item["name"]
    static = item["static_status"]
    if name in NONDECISION_CONTROLLER:
        return "NONDECISION_EXECUTION_PRESENTATION_OR_CONTROL", True
    if name in NONPRODUCTION_COMMANDER_CONTROLLER:
        return "NONPRODUCTION_COMMANDER_FAIL_CLOSED", True
    if static == "TYPED_EXTERNALIZED_STATIC":
        return "DISCRETIONARY_TYPED_EXTERNAL", True
    if static == "DELEGATES_TO_TYPED_EXTERNAL_STATIC":
        return "DISCRETIONARY_DELEGATES_TYPED_EXTERNAL", True
    if static == "GUI_ADAPTER_DEPENDENT_STATIC":
        return "DISCRETIONARY_TYPED_GUI_ADAPTER", True
    if name in EXPLICIT_DELEGATED_OR_STATE_MACHINE:
        return "DISCRETIONARY_FORGE_STATE_MACHINE_OR_TYPED_DELEGATE", True
    return "UNKNOWN", False


def gui_route(item: dict) -> tuple[str, bool]:
    name = item["name"]
    if name in GUI_PRESENTATION_NONDECISION:
        return "NONDECISION_PRESENTATION", True
    if name in GUI_NONPRODUCTION_COMMANDER:
        return "NONPRODUCTION_COMMANDER_FAIL_CLOSED", True
    if name in GUI_TYPED_CONTROLLER_BYPASS:
        return "DISCRETIONARY_TYPED_CONTROLLER_BYPASS", True
    if name in GUI_STRICT_UNREACHABLE_HELPER:
        return "STRICT_UNREACHABLE_BEHIND_TYPED_CONTROLLER_PATH", True
    if name in GUI_TYPED_ADAPTER:
        return "DISCRETIONARY_TYPED_GUI_ADAPTER", True
    return "UNKNOWN", False


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--implementation", required=True, type=Path)
    parser.add_argument("--tape", required=True, type=Path)
    parser.add_argument("--forge-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()

    impl = json.loads(args.implementation.read_text())
    tape = json.loads(args.tape.read_text())
    forge = args.forge_root
    controller_source = (forge / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java").read_text()
    sync_source = (forge / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSyncronizedBase.java").read_text()
    mana_source = (forge / "forge-gui/src/main/java/forge/gamemodes/match/input/InputPayMana.java").read_text()
    gui_adapter = (forge / "forge-gui/src/main/java/forge/player/ExternalDecisionGuiAdapter.java").read_text()
    target_input_source = (forge / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSelectTargets.java").read_text()
    target_selection_source = (forge / "forge-gui/src/main/java/forge/player/TargetSelection.java").read_text()

    callbacks = []
    untyped = []
    for item in impl["census"]["player_controller_callback_census"]:
        route, covered = controller_route(item)
        row = dict(item)
        row["semantic_class"] = route
        row["production_reachable"] = item["name"] not in NONPRODUCTION_COMMANDER_CONTROLLER
        row["typed_or_nondecision_covered"] = covered
        callbacks.append(row)
        if row["production_reachable"] and route.startswith("DISCRETIONARY") and not covered:
            untyped.append(row["callback_id"])
        if route == "UNKNOWN":
            untyped.append(row["callback_id"])

    gui_rows = []
    unclassified_gui = []
    for item in impl["census"]["remote_protocol_blocking_decision_census"]:
        route, covered = gui_route(item)
        row = dict(item)
        row["semantic_class"] = route
        row["production_reachable"] = item["name"] not in GUI_NONPRODUCTION_COMMANDER
        row["typed_or_nondecision_covered"] = covered
        gui_rows.append(row)
        if not covered:
            unclassified_gui.append(item["name"])

    fallback_assertions = {
        "priority_is_explicit": '"PRIORITY_ACTION"' in controller_source and "chooseExternalPriorityAction" in controller_source,
        "legacy_autopass_disabled": "if (hasExternalDecisionProvider())" in controller_source and "public void autoPassCancel()" in controller_source,
        "cost_reduction_default_bypassed": "external cost reduction" in controller_source,
        "remembered_color_bypassed": '"COLOR_SELECTION"' in controller_source,
        "remembered_simultaneous_order_bypassed": '"SIMULTANEOUS_ABILITY_ORDER"' in controller_source,
        "replacement_first_fallback_bypassed": '"REPLACEMENT_ORDER"' in controller_source and "chooseExternalDiscrete(possibleReplacers" in controller_source,
        "divided_amount_gui_bypassed": '"DIVIDED_TARGET_ALLOCATION"' in controller_source,
        "combat_damage_gui_bypassed": '"COMBAT_DAMAGE_ASSIGNMENT"' in controller_source,
        "shield_and_mana_combo_gui_bypassed": '"SHIELD_DIVISION"' in controller_source and '"MANA_COMBINATION"' in controller_source,
        "attack_and_block_inputs_driven": '"DECLARE_ATTACKERS"' in controller_source and '"DECLARE_BLOCKERS"' in controller_source,
        "target_input_driven": "public void driveExternal()" in target_input_source and "inp.driveExternal();" in target_selection_source,
        "entity_inputs_driven": "InputSelectEntitiesFromList<?> entitySelection" in sync_source and "entitySelection.driveExternal()" in sync_source,
        "mana_input_driven_without_ai_autopay": "InputPayMana manaPayment" in sync_source and "manaPayment.driveExternal()" in sync_source and "AI mana autopay is forbidden in strict external mode" in mana_source,
        "convoke_input_driven": "InputSelectCardsForConvokeOrImprovise convokeSelection" in sync_source and "convokeSelection.driveExternal()" in sync_source,
        "free_form_input_fail_closed": "free-form GUI input has no exact authoritative option set" in gui_adapter,
        "unmodelled_gui_fail_closed": "unmodelled GUI operation is blocked" in gui_adapter,
        "sideboard_fail_closed": 'case "sideboard"' in gui_adapter and "legacy GUI operation lacks an exact typed response schema" in gui_adapter,
        "manipulate_fail_closed": 'case "manipulateCardList"' in gui_adapter,
    }

    events = tape.get("events", [])
    runtime_tape_qualified = (
        tape.get("schema") == "commander-simulator-next.full-game-decision-tape.v1"
        and tape.get("player_count") == 4
        and tape.get("format") == "Commander"
        and tape.get("game_completed") is True
        and tape.get("event_count") == len(events)
        and len(events) > 0
        and all(event.get("response_status") == "ACCEPTED" for event in events)
        and {event.get("actor_id") for event in events} == {0, 1, 2, 3}
        and {"MULLIGAN", "PRIORITY_ACTION", "STARTING_PLAYER"}.issubset(
            {event.get("decision_kind") for event in events}
        )
    )

    controller_complete = len(callbacks) == 109 and len({x["callback_id"] for x in callbacks}) == 109 and not untyped
    gui_complete = len(gui_rows) == 15 and len({x["name"] for x in gui_rows}) == 15 and not unclassified_gui
    fallback_violations = [name for name, passed in fallback_assertions.items() if not passed]
    production_reachable_untyped = len(set(untyped))
    production_reachable_fallback = len(fallback_violations)

    result = {
        "schema": "commander-simulator-next.ws01-semantic-decision-census.v1",
        "source_head": impl["source_head"],
        "source_tree": impl["source_tree"],
        "forge_pin": impl["forge_pin"],
        "controller_callback_declarations_classified": len(callbacks),
        "blocking_gui_decisions_classified": len(gui_rows),
        "controller_semantic_census_complete": controller_complete,
        "blocking_gui_semantic_census_complete": gui_complete,
        "production_reachable_untyped_decisions": production_reachable_untyped,
        "production_reachable_fallback_decisions": production_reachable_fallback,
        "full_game_decision_tape_emitted": runtime_tape_qualified,
        "full_game_event_count": len(events),
        "full_game_turn_count": tape.get("turn_count"),
        "full_game_response_status_counts": dict(Counter(e.get("response_status") for e in events)),
        "full_game_decision_kind_counts": dict(Counter(e.get("decision_kind") for e in events)),
        "fallback_assertions": fallback_assertions,
        "fallback_violations": fallback_violations,
        "untyped_or_unknown_callbacks": sorted(set(untyped)),
        "unclassified_gui_paths": sorted(set(unclassified_gui)),
        "controller_semantic_classification_counts": dict(Counter(x["semantic_class"] for x in callbacks)),
        "blocking_gui_semantic_classification_counts": dict(Counter(x["semantic_class"] for x in gui_rows)),
        "controller_callbacks": callbacks,
        "blocking_gui_paths": gui_rows,
        "status": "PASS" if controller_complete and gui_complete and production_reachable_untyped == 0
            and production_reachable_fallback == 0 and runtime_tape_qualified else "FAIL",
    }
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "status": result["status"],
        "controller": len(callbacks),
        "gui": len(gui_rows),
        "untyped": production_reachable_untyped,
        "fallbacks": production_reachable_fallback,
        "tape": runtime_tape_qualified,
    }, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
