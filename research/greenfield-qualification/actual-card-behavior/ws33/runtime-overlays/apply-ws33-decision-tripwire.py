#!/usr/bin/env python3
"""Add an observation-only WS33 AI-decision tripwire to pinned Forge.

The tripwire is inert unless a qualification test registers an observer.
It records (not blocks) invocations of the discretionary decision methods
reachable during spell/ability resolution on the AI test controller. A
STATE_ONLY witness must observe zero hits; any hit fails the record
closed with an explicit unexpected-decision root cause.

Covered sites (all in PlayerControllerAi.java, each one insertion):
chooseTargetsFor, chooseCardsForEffect, chooseCardsForEffectMultiple,
chooseSingleEntityForEffect, confirmAction, chooseNumber (3 overloads),
chooseSpellAbilityToPlay.

Scope note: methods outside this set are not observed. Batch selection
combines this runtime surface with a structural script screen (no
decision/target/RNG/hidden fields on the executed chain) and exact
semantic postconditions. Coverage is recorded per record; residual risk
outside the covered set stays CODE_DERIVED, never PASS-inherited.
"""
from __future__ import annotations

import argparse
from pathlib import Path

SITES = [
    "chooseTargetsFor",
    "chooseCardsForEffect",
    "chooseCardsForEffectMultiple",
    "chooseSingleEntityForEffect",
    "confirmAction",
    "chooseNumber",
    "chooseSpellAbilityToPlay",
]


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"WS33_DECISION_TRIPWIRE_OVERLAY=FAIL {label}: expected one match, got {n}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    path = args.forge_root / "forge-ai/src/main/java/forge/ai/PlayerControllerAi.java"
    s = path.read_text(encoding="utf-8")
    if "setWs33DecisionTripwire" in s:
        raise SystemExit("WS33_DECISION_TRIPWIRE_OVERLAY=FAIL overlay already present")
    s = replace_once(
        s,
        "public class PlayerControllerAi extends PlayerController {\n    private final AiController brains;",
        "public class PlayerControllerAi extends PlayerController {\n    private static volatile Consumer<String> ws33DecisionTripwire;\n\n    public static void setWs33DecisionTripwire(final Consumer<String> tripwire) {\n        ws33DecisionTripwire = tripwire;\n    }\n\n    private static void ws33NoteDecision(final String site) {\n        final Consumer<String> tripwire = ws33DecisionTripwire;\n        if (tripwire != null) {\n            tripwire.accept(site);\n        }\n    }\n\n    private final AiController brains;",
        "tripwire slot",
    )
    import re
    # Insert a probe as the first statement of every covered method by
    # matching the method signature line followed by its opening brace.
    # Signatures below are exact pin content (verified); each must match once
    # except chooseNumber which has three overloads.
    signatures = [
        "    public boolean chooseTargetsFor(SpellAbility currentAbility) {",
        "    public CardCollectionView chooseCardsForEffect(CardCollectionView sourceList, SpellAbility sa, String title, int min, int max, boolean isOptional, Map<String, Object> params) {",
        "    public CardCollection chooseCardsForEffectMultiple(Map<String, CardCollection> validMap, SpellAbility sa, String title, boolean isOptional) {",
        "    public <T extends GameEntity> T chooseSingleEntityForEffect(FCollectionView<T> optionList, DelayedReveal delayedReveal, SpellAbility sa, String title, boolean isOptional, Player targetedPlayer, Map<String, Object> params) {",
        "    public boolean confirmAction(SpellAbility sa, PlayerActionConfirmMode mode, String message, List<String> options, Card cardToShow, Map<String, Object> params) {",
        "    public List<SpellAbility> chooseSpellAbilityToPlay() {",
        "    public int chooseNumber(SpellAbility sa, String title, int min, int max) {",
        "    public int chooseNumber(SpellAbility sa, String string, int min, int max, Map<String, Object> params) {",
        "    public int chooseNumber(SpellAbility sa, String title, List<Integer> options, Player relatedPlayer) {",
    ]
    probed = 0
    for sig in signatures:
        method = re.search(r"\b(\w+)\(", sig).group(1)
        old = sig + "\n"
        new = sig + '\n        ws33NoteDecision("' + method + '");\n'
        n = s.count(old)
        if n != 1:
            raise SystemExit(
                f"WS33_DECISION_TRIPWIRE_OVERLAY=FAIL site {method}: expected one match, got {n}")
        s = s.replace(old, new, 1)
        probed += 1
    path.write_text(s, encoding="utf-8")
    print(f"WS33_DECISION_TRIPWIRE_OVERLAY=PASS sites={probed} observation_only=TRUE "
          f"methods={','.join(SITES)}")


if __name__ == "__main__":
    main()
