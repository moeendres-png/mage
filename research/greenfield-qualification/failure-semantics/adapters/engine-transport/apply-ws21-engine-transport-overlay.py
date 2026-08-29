#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS21 expected exactly one anchor in {path}, found {count}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def copy_new(src: Path, dst: Path) -> None:
    if dst.exists():
        raise SystemExit(f"WS21 refusing to overwrite unexpected file: {dst}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("forge_root")
    parser.add_argument("ws21_root")
    args = parser.parse_args()
    forge = Path(args.forge_root).resolve()
    root = Path(args.ws21_root).resolve()
    overlay = root / "research/greenfield-qualification/failure-semantics/adapters/engine-transport/forge-overlay"

    for rel in (
        "forge/game/Ws21EngineExecutionException.java",
        "forge/game/Ws21EngineFaultInjector.java",
    ):
        copy_new(overlay / rel, forge / "forge-game/src/main/java" / rel)
    for rel in (
        "forge/gamemodes/match/input/ExternalDecisionTransportException.java",
        "forge/gamemodes/match/input/Ws21DecisionCommitProbe.java",
    ):
        copy_new(overlay / rel, forge / "forge-gui/src/main/java" / rel)
    for name in (
        "Ws21PilotWire.java",
        "Ws21PilotTransport.java",
        "Ws21FailureWorker.java",
        "Ws21FailureQualificationTest.java",
    ):
        copy_new(overlay / "forge/net" / name,
                 forge / "forge-gui-desktop/src/test/java/forge/net" / name)

    game_action = forge / "forge-game/src/main/java/forge/game/GameAction.java"
    anchor = (
        "    private Card changeZone(final Zone zoneFrom, Zone zoneTo, final Card c, Integer position, "
        "SpellAbility cause, Map<AbilityKey, Object> params) {\n"
    )
    replace_once(
        game_action,
        anchor,
        anchor
        + "        Ws21EngineFaultInjector.maybeFail(\"forge.game.GameAction.changeZone:entry\");\n"
        + "        Ws21EngineFaultInjector.markOriginalBodyEntry();\n",
    )

    controller = forge / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    controller_text = controller.read_text(encoding="utf-8")
    required_ws01_factory = (
        "private static volatile Function<Player, ExternalDecisionProvider> externalDecisionProviderFactory;",
        "public static void setExternalDecisionProviderFactory(final Function<Player, ExternalDecisionProvider> factory)",
    )
    for marker in required_ws01_factory:
        if marker not in controller_text:
            raise SystemExit(f"WS21 requires authoritative WS01 provider factory marker: {marker}")

    replace_once(
        controller,
        "                cancelAllowed, constraints, responseSchema, semanticContext);\n        try {\n",
        "                cancelAllowed, constraints, responseSchema, semanticContext);\n"
        "        Ws21DecisionCommitProbe.recordOpen(request);\n"
        "        try {\n",
    )
    replace_once(
        controller,
        "                final Throwable cause = ex.getCause();\n"
        "                final ExternalDecisionValidationException error = cause instanceof ExternalDecisionValidationException typed\n",
        "                final Throwable cause = ex.getCause();\n"
        "                if (cause instanceof ExternalDecisionTransportException transportFailure) {\n"
        "                    Ws21DecisionCommitProbe.recordTransportPropagation(request, transportFailure);\n"
        "                    throw transportFailure;\n"
        "                }\n"
        "                final ExternalDecisionValidationException error = cause instanceof ExternalDecisionValidationException typed\n",
    )
    replace_once(
        controller,
        "            externalDecisionTape.validateAndRecord(request, response, token, actor.getId(), principal.getId(), false);\n"
        "            return response;\n",
        "            externalDecisionTape.validateAndRecord(request, response, token, actor.getId(), principal.getId(), false);\n"
        "            Ws21DecisionCommitProbe.recordValidated(request);\n"
        "            return response;\n",
    )
    replace_once(
        controller,
        "            if (response.isCancel()) {\n"
        "                input.applyExternalCancel();\n"
        "            } else {\n"
        "                input.applyExternalSelection(response.getSelectedOptionIds());\n"
        "            }\n"
        "            input.awaitLatchRelease();\n",
        "            if (response.isCancel()) {\n"
        "                input.applyExternalCancel();\n"
        "            } else {\n"
        "                input.applyExternalSelection(response.getSelectedOptionIds());\n"
        "            }\n"
        "            Ws21DecisionCommitProbe.recordApplied(response.getDecisionId(), response.getPrincipalId());\n"
        "            input.awaitLatchRelease();\n",
    )

    print("WS21_ENGINE_TRANSPORT_OVERLAY_APPLIED=TRUE")
    print("WS21_ENGINE_FAULT_SITE=forge.game.GameAction.changeZone:entry")
    print("WS21_TRANSPORT_EXCEPTION_PRESERVED=TRUE")
    print("WS21_DECISION_COMMIT_PROBE=TRUE")
    print("WS21_WS01_PROVIDER_FACTORY_REUSED=TRUE")
    print("WS21_PROCESS_MODEL=ONE_GAME_PER_OS_PROCESS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
