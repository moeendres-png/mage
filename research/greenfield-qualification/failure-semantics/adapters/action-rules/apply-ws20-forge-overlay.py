#!/usr/bin/env python3
"""Apply the WS20 action/rules failure adapters after WS01 + WS12 overlays."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"unexpected exact-pin structure for {label}: count={text.count(old)}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()

    root = args.forge_root.resolve()
    here = Path(__file__).resolve().parent
    overlay = here / "forge-overlay"

    game_main = root / "forge-game/src/main/java/forge/game"
    gui_main = root / "forge-gui/src/main/java/forge/gamemodes/match/input"
    gui_test = root / "forge-gui/src/test/java/forge/gamemodes/match/input"
    player_controller = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    game_action = root / "forge-game/src/main/java/forge/game/GameAction.java"

    required = [
        gui_main / "UnifiedOutcome.java",
        gui_main / "ExternalDecisionResponse.java",
        player_controller,
        game_action,
    ]
    for path in required:
        if not path.exists():
            raise SystemExit(f"required prior overlay/source missing: {path}")

    for name in ("Ws20FailureSignal.java", "Ws20FailureException.java", "Ws20RulesPathBoundary.java"):
        shutil.copy2(overlay / name, game_main / name)
    shutil.copy2(overlay / "Ws20ActionCompletionBoundary.java", gui_main / "Ws20ActionCompletionBoundary.java")
    shutil.copy2(overlay / "Ws20FailureAdaptersContractTest.java", gui_test / "Ws20FailureAdaptersContractTest.java")

    controller = player_controller.read_text(encoding="utf-8")
    controller_old = """            final ExternalDecisionResponse response = requestExternalSelection(decisionKind, options, min, effectiveMax,
                    cancelAllowed, ExternalDecisionRequest.RESPONSE_SCHEMA, constraints, context);
            if (response.isCancel()) {
"""
    controller_new = """            final ExternalDecisionResponse response = requestExternalSelection(decisionKind, options, min, effectiveMax,
                    cancelAllowed, ExternalDecisionRequest.RESPONSE_SCHEMA, constraints, context);
            // WS20: the response was legal when accepted, but the selected engine
            // identity must still be current immediately before Input mutation.
            Ws20ActionCompletionBoundary.requireCompletable(getGame(), response, optionList);
            if (response.isCancel()) {
"""
    controller = replace_once(controller, controller_old, controller_new,
                              "PlayerControllerHuman external entity application boundary")
    player_controller.write_text(controller, encoding="utf-8")

    action = game_action.read_text(encoding="utf-8")
    todo = "//TODO: Figure out what on earth happens if you animate an attraction, mutate a creature/commander/token onto it, and it dies..."
    todo_index = action.find(todo)
    if todo_index < 0:
        raise SystemExit("exact-pin Astrotorium merged-object TODO not found")
    return_line = "            return moveToJunkyard(c, cause, params);"
    return_index = action.find(return_line, todo_index)
    if return_index < 0 or return_index - todo_index > 800:
        raise SystemExit("exact-pin Astrotorium junkyard boundary not found near TODO")
    guard = """            if (c.hasMergedCard()) {
                final Player ws20Principal = c.getController() != null ? c.getController() : c.getOwner();
                return Ws20RulesPathBoundary.unsupportedAstrotoriumMergedZoneChange(
                        "forge-game:" + game.getId(), ws20Principal.getId());
            }
"""
    action = action[:return_index] + guard + action[return_index:]
    game_action.write_text(action, encoding="utf-8")

    print("WS20_FORGE_OVERLAY=APPLIED")
    print("WS20_ACTION_BOUNDARY=PlayerControllerHuman.chooseExternalEntities:pre-Input-apply")
    print("WS20_RULES_BOUNDARY=GameAction.changeZone:Astrotorium-merged-object")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
