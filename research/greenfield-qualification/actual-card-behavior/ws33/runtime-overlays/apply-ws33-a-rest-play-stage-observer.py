#!/usr/bin/env python3
"""Expose observation-only PlaySpellAbility stage callbacks for WS33 A-rest.

This patch is applied after apply-ws33-stack-resolution-reachability.py to the ephemeral
pinned-Forge checkout. It does not change any boolean, order, cost, target, timing, or
stack result. It only reports the already-computed PlaySpellAbility stage/result.
"""
from __future__ import annotations
import argparse
from pathlib import Path


def require(c: bool, m: str) -> None:
    if not c:
        raise SystemExit("WS33_A_REST_PLAY_STAGE_OBSERVER=FAIL " + m)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    require(n == 1, f"{label}: expected exactly one match, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    path = args.forge_root / "forge-game/src/main/java/forge/game/player/PlaySpellAbility.java"
    src = path.read_text(encoding="utf-8")

    anchor = '''    private static void ws33TraceTriggerPlay(final String stage, final SpellAbility ability) {\n        if (ability == null || !ability.isTrigger()) {\n            return;\n        }\n        final Card host = ability.getHostCard();\n        System.err.println("WS33_TRIGGER_PLAY\\t" + stage + "\\tNA\\t" + ability.getId() + "\\t" + ability.getSourceTrigger() + "\\t" + (host == null ? -1 : host.getId()) + "\\t" + (ability.getApi() == null ? "" : ability.getApi().name()) + "\\t" + ability.getClass().getName());\n    }\n\n    private static boolean ws33TraceTriggerStage(final String stage, final SpellAbility ability, final boolean result) {\n        if (ability != null && ability.isTrigger()) {\n            final Card host = ability.getHostCard();\n            System.err.println("WS33_TRIGGER_PLAY\\t" + stage + "\\t" + result + "\\t" + ability.getId() + "\\t" + ability.getSourceTrigger() + "\\t" + (host == null ? -1 : host.getId()) + "\\t" + (ability.getApi() == null ? "" : ability.getApi().name()) + "\\t" + ability.getClass().getName());\n        }\n        return result;\n    }\n\n'''
    replacement = '''    @FunctionalInterface\n    public interface Ws33PlayStageObserver {\n        void onStage(String stage, SpellAbility ability, boolean result);\n    }\n\n    private static volatile Ws33PlayStageObserver ws33PlayStageObserver;\n\n    public static void setWs33PlayStageObserver(final Ws33PlayStageObserver observer) {\n        ws33PlayStageObserver = observer;\n    }\n\n    private static void ws33ObservePlayStage(final String stage, final SpellAbility ability, final boolean result) {\n        final Ws33PlayStageObserver observer = ws33PlayStageObserver;\n        if (observer != null) {\n            observer.onStage(stage, ability, result);\n        }\n    }\n\n    private static void ws33TraceTriggerPlay(final String stage, final SpellAbility ability) {\n        if (ability == null) {\n            return;\n        }\n        ws33ObservePlayStage(stage, ability, true);\n        final Card host = ability.getHostCard();\n        System.err.println("WS33_PLAY_ABILITY_STAGE\\t" + stage + "\\tNA\\t" + ability.getId() + "\\t" + ability.getSourceTrigger() + "\\t" + (host == null ? -1 : host.getId()) + "\\t" + (ability.getApi() == null ? "" : ability.getApi().name()) + "\\t" + ability.getClass().getName());\n    }\n\n    private static boolean ws33TraceTriggerStage(final String stage, final SpellAbility ability, final boolean result) {\n        if (ability != null) {\n            ws33ObservePlayStage(stage, ability, result);\n            final Card host = ability.getHostCard();\n            System.err.println("WS33_PLAY_ABILITY_STAGE\\t" + stage + "\\t" + result + "\\t" + ability.getId() + "\\t" + ability.getSourceTrigger() + "\\t" + (host == null ? -1 : host.getId()) + "\\t" + (ability.getApi() == null ? "" : ability.getApi().name()) + "\\t" + ability.getClass().getName());\n        }\n        return result;\n    }\n\n'''
    src = replace_once(src, anchor, replacement, "post-stack-reachability helper")
    for token in (
        "public interface Ws33PlayStageObserver",
        "setWs33PlayStageObserver",
        "ws33ObservePlayStage(stage, ability, result)",
        "WS33_PLAY_ABILITY_STAGE",
    ):
        require(token in src, "missing token " + token)
    require("return result;" in src, "stage wrapper no longer returns original result")
    path.write_text(src, encoding="utf-8")
    print("WS33_A_REST_PLAY_STAGE_OBSERVER=PASS semantics_mutated=FALSE booleans_mutated=FALSE")


if __name__ == "__main__":
    main()
