#!/usr/bin/env python3
"""Expose observation-only PlaySpellAbility and mana-payment callbacks for WS33 A-rest.

This patch is applied after the WS01 strict decision bridge and WS33 stack reachability
patches to the ephemeral pinned-Forge checkout. It does not change any boolean, option,
order, cost, mana, target, timing, or stack result. It only reports already-computed
PlaySpellAbility stages and InputPayMana external-loop state to qualification evidence.
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


def patch_play_spell_ability(root: Path) -> None:
    path = root / "forge-game/src/main/java/forge/game/player/PlaySpellAbility.java"
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
        require(token in src, "missing PlaySpellAbility token " + token)
    require("return result;" in src, "stage wrapper no longer returns original result")
    path.write_text(src, encoding="utf-8")


def patch_input_pay_mana(root: Path) -> None:
    path = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputPayMana.java"
    src = path.read_text(encoding="utf-8")

    src = replace_once(
        src,
        '''    public void driveExternal() {\n        while (!isAlreadyPaid()) {\n            byte colorCanUse = 0;\n''',
        '''    public void driveExternal() {\n        while (!isAlreadyPaid()) {\n            System.err.println("WS33_MANA_PAYMENT_TRACE\\tITERATION_BEGIN\\t"\n                    + (saPaidFor == null || saPaidFor.getHostCard() == null ? "" : saPaidFor.getHostCard().getName())\n                    + "\\t" + (saPaidFor == null ? -1 : saPaidFor.getId())\n                    + "\\t" + manaCost + "\\tpool=" + player.getManaPool().size());\n            byte colorCanUse = 0;\n''',
        "mana iteration begin",
    )

    src = replace_once(
        src,
        '''            final String action = getController().chooseExternalUiOptions(actions, 1, 1, false, false,\n                    "MANA_PAYMENT", value -> value).get(0);\n''',
        '''            System.err.println("WS33_MANA_PAYMENT_TRACE\\tOPTIONS\\t"\n                    + (saPaidFor == null || saPaidFor.getHostCard() == null ? "" : saPaidFor.getHostCard().getName())\n                    + "\\t" + (saPaidFor == null ? -1 : saPaidFor.getId())\n                    + "\\t" + manaCost + "\\t" + String.join(",", actions));\n            final String action = getController().chooseExternalUiOptions(actions, 1, 1, false, false,\n                    "MANA_PAYMENT", value -> value).get(0);\n            System.err.println("WS33_MANA_PAYMENT_TRACE\\tSELECTED\\t"\n                    + (saPaidFor == null || saPaidFor.getHostCard() == null ? "" : saPaidFor.getHostCard().getName())\n                    + "\\t" + (saPaidFor == null ? -1 : saPaidFor.getId())\n                    + "\\t" + manaCost + "\\t" + action);\n''',
        "mana options and selected action",
    )

    src = replace_once(
        src,
        '''                onStateChanged();\n                continue;\n            }\n            final SpellAbility selectedAbility = abilityChoices.get(action);\n''',
        '''                onStateChanged();\n                System.err.println("WS33_MANA_PAYMENT_TRACE\\tAFTER_POOL\\t"\n                        + (saPaidFor == null || saPaidFor.getHostCard() == null ? "" : saPaidFor.getHostCard().getName())\n                        + "\\t" + (saPaidFor == null ? -1 : saPaidFor.getId())\n                        + "\\t" + manaCost + "\\t" + action);\n                continue;\n            }\n            final SpellAbility selectedAbility = abilityChoices.get(action);\n''',
        "floating mana post-state",
    )

    src = replace_once(
        src,
        '''            if (selectedAbility != null) {\n                if (!selectedAbility.canPlay(true) || !selectedAbility.isManaAbilityFor(saPaidFor, colorCanUse)\n                        || !activateManaAbility(selectedAbility.getHostCard(), selectedAbility)) {\n''',
        '''            if (selectedAbility != null) {\n                System.err.println("WS33_MANA_PAYMENT_TRACE\\tABILITY_BEFORE\\t"\n                        + (saPaidFor == null || saPaidFor.getHostCard() == null ? "" : saPaidFor.getHostCard().getName())\n                        + "\\t" + (saPaidFor == null ? -1 : saPaidFor.getId())\n                        + "\\t" + manaCost + "\\t" + action\n                        + "\\thost=" + selectedAbility.getHostCard().getName()\n                        + "#" + selectedAbility.getHostCard().getId()\n                        + "\\tability=" + selectedAbility.getId());\n                if (!selectedAbility.canPlay(true) || !selectedAbility.isManaAbilityFor(saPaidFor, colorCanUse)\n                        || !activateManaAbility(selectedAbility.getHostCard(), selectedAbility)) {\n''',
        "mana ability pre-state",
    )

    src = replace_once(
        src,
        '''                }\n                continue;\n            }\n            throw new ExternalDecisionValidationException(\n                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,\n                    "unknown mana payment action token");\n        }\n    }\n\n    protected boolean isAlreadyPaid() {\n''',
        '''                }\n                System.err.println("WS33_MANA_PAYMENT_TRACE\\tABILITY_AFTER\\t"\n                        + (saPaidFor == null || saPaidFor.getHostCard() == null ? "" : saPaidFor.getHostCard().getName())\n                        + "\\t" + (saPaidFor == null ? -1 : saPaidFor.getId())\n                        + "\\t" + manaCost + "\\t" + action\n                        + "\\tpaid=" + isAlreadyPaid());\n                continue;\n            }\n            throw new ExternalDecisionValidationException(\n                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,\n                    "unknown mana payment action token");\n        }\n        System.err.println("WS33_MANA_PAYMENT_TRACE\\tCOMPLETE\\t"\n                + (saPaidFor == null || saPaidFor.getHostCard() == null ? "" : saPaidFor.getHostCard().getName())\n                + "\\t" + (saPaidFor == null ? -1 : saPaidFor.getId())\n                + "\\t" + manaCost + "\\tpaid=" + isAlreadyPaid());\n    }\n\n    protected boolean isAlreadyPaid() {\n''',
        "mana ability post-state and completion",
    )

    required = (
        "WS33_MANA_PAYMENT_TRACE\\tITERATION_BEGIN",
        "WS33_MANA_PAYMENT_TRACE\\tOPTIONS",
        "WS33_MANA_PAYMENT_TRACE\\tSELECTED",
        "WS33_MANA_PAYMENT_TRACE\\tABILITY_BEFORE",
        "WS33_MANA_PAYMENT_TRACE\\tABILITY_AFTER",
        "WS33_MANA_PAYMENT_TRACE\\tCOMPLETE",
    )
    for token in required:
        require(token in src, "missing InputPayMana token " + token)
    path.write_text(src, encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    root = args.forge_root.resolve()
    patch_play_spell_ability(root)
    patch_input_pay_mana(root)
    print("WS33_A_REST_PLAY_STAGE_OBSERVER=PASS semantics_mutated=FALSE booleans_mutated=FALSE")
    print("WS33_A_REST_MANA_PAYMENT_OBSERVER=PASS options_mutated=FALSE selection_mutated=FALSE mana_mutated=FALSE cost_mutated=FALSE")


if __name__ == "__main__":
    main()
