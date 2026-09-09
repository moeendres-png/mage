#!/usr/bin/env python3
"""Add an observation-only WS33 AI-decision tripwire to pinned Forge.

The tripwire is inert unless a qualification test registers an observer.
It records (not blocks) invocations of the discretionary decision methods
reachable during spell/ability resolution on the AI test controller, along
with the caller-supplied option count (-1 where no option set is visible
at the probe). A STATE_ONLY witness must show zero undeclared,
non-incidental hits; declared singleton consultations (e.g. Attach target
reaffirmation over a one-member defined set) are recorded with their
option count and adjudicated against the case declaration.

Covered sites (all in PlayerControllerAi.java):
chooseTargetsFor, chooseCardsForEffect, chooseCardsForEffectMultiple,
chooseSingleEntityForEffect, confirmAction, chooseNumber (3 overloads),
chooseSpellAbilityToPlay.

Scope note: methods outside this set are not observed. Batch selection
combines this runtime surface with a structural script screen and exact
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

# (method anchor substring, probe options expression). Anchors are matched
# against exact pin content; each anchor must occur exactly once except
# chooseNumber which occurs once per overload (3).
PROBES = [
    ("    public boolean chooseTargetsFor(SpellAbility currentAbility) {",
     "-1"),
    ("    public CardCollectionView chooseCardsForEffect(CardCollectionView sourceList, SpellAbility sa, String title, int min, int max, boolean isOptional, Map<String, Object> params) {",
     "sourceList == null ? -1 : sourceList.size()"),
    ("    public CardCollection chooseCardsForEffectMultiple(Map<String, CardCollection> validMap, SpellAbility sa, String title, boolean isOptional) {",
     "validMap == null ? -1 : validMap.size()"),
    ("    public <T extends GameEntity> T chooseSingleEntityForEffect(FCollectionView<T> optionList, DelayedReveal delayedReveal, SpellAbility sa, String title, boolean isOptional, Player targetedPlayer, Map<String, Object> params) {",
     "optionList == null ? -1 : optionList.size()"),
    ("    public boolean confirmAction(SpellAbility sa, PlayerActionConfirmMode mode, String message, List<String> options, Card cardToShow, Map<String, Object> params) {",
     "options == null ? -1 : options.size()"),
    ("    public List<SpellAbility> chooseSpellAbilityToPlay() {",
     "-1"),
    ("    public int chooseNumber(SpellAbility sa, String title, int min, int max) {",
     "(max >= min ? (max - min + 1) : 0)"),
    ("    public int chooseNumber(SpellAbility sa, String string, int min, int max, Map<String, Object> params) {",
     "(max >= min ? (max - min + 1) : 0)"),
    ("    public int chooseNumber(SpellAbility sa, String title, List<Integer> options, Player relatedPlayer) {",
     "options == null ? -1 : options.size()"),
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
        "import java.util.function.Consumer;",
        "import java.util.function.BiConsumer;\nimport java.util.function.Consumer;",
        "BiConsumer import",
    )
    s = replace_once(
        s,
        "public class PlayerControllerAi extends PlayerController {\n    private final AiController brains;",
        "public class PlayerControllerAi extends PlayerController {\n    private static volatile BiConsumer<String, Integer> ws33DecisionTripwire;\n\n    public static void setWs33DecisionTripwire(final BiConsumer<String, Integer> tripwire) {\n        ws33DecisionTripwire = tripwire;\n    }\n\n    private static void ws33NoteDecision(final String site, final int options) {\n        final BiConsumer<String, Integer> tripwire = ws33DecisionTripwire;\n        if (tripwire != null) {\n            tripwire.accept(site, options);\n        }\n    }\n\n    private final AiController brains;",
        "tripwire slot",
    )
    for sig, expr in PROBES:
        method = sig.split("(")[0].rsplit(" ", 1)[-1]
        old = sig + "\n"
        new = sig + '\n        ws33NoteDecision("' + method + '", ' + expr + ');\n'
        s = replace_once(s, old, new, f"site {method}")
    path.write_text(s, encoding="utf-8")
    print("WS33_DECISION_TRIPWIRE_OVERLAY=PASS sites=9 observation_only=TRUE "
          f"methods={','.join(SITES)} options_counted=TRUE")


if __name__ == "__main__":
    main()
