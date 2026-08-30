#!/usr/bin/env python3
"""ACTION_COST_DECISION dependency overlay for WS31 single-target paths.

The overlay is applied only after the exact WS01 strict-decision patch. It adds
one generic rules-core adapter class: mandatory single-target GameEntity choices
from non-stack zones. Multi-target, divided, stack-target and random-target
selection remain fail-closed.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("forge_root", type=Path)
    ns = ap.parse_args()
    p = ns.forge_root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    text = p.read_text(encoding="utf-8")

    text = once(
        text,
        "import forge.game.staticability.StaticAbilityMode;",
        "import forge.game.staticability.StaticAbilityMode;\nimport forge.game.staticability.StaticAbilityMustTarget;",
        "StaticAbilityMustTarget import",
    )

    old = '''    @Override
    public boolean chooseTargetsFor(final SpellAbility currentAbility) {
        rejectExternalDecision("TARGET_SELECTION");
        final TargetSelection select = new TargetSelection(this, currentAbility);
'''
    new = '''    @Override
    public boolean chooseTargetsFor(final SpellAbility currentAbility) {
        if (hasExternalDecisionProvider()) {
            final TargetRestrictions tgt = currentAbility.getTargetRestrictions();
            if (tgt == null || !currentAbility.usesTargeting()) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "TARGET_SELECTION: ability does not expose target restrictions");
            }
            if (currentAbility.getMinTargets() != 1 || currentAbility.getMaxTargets() != 1
                    || currentAbility.isDividedAsYouChoose()
                    || tgt.getZone().contains(ZoneType.Stack)
                    || tgt.isRandomTarget() || tgt.isRandomNumTargets()
                    || tgt.isDifferentControllers() || tgt.isForEachPlayer()) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "TARGET_SELECTION: only mandatory single non-stack targets are qualified by this adapter");
            }

            final List<GameEntity> candidates = new ArrayList<>(tgt.getAllCandidates(currentAbility));
            candidates.removeIf(candidate -> !currentAbility.canTarget(candidate));

            // Preserve Forge's must-target rules before exposing options. The pilot receives
            // only the authoritative post-filter set and never reconstructs target legality.
            final List<Card> mustTargetCards = CardUtil.getValidCardsToTarget(currentAbility);
            final boolean mustTargetFiltered = StaticAbilityMustTarget.filterMustTargetCards(
                    getPlayer(), mustTargetCards, currentAbility);
            if (mustTargetFiltered && !mustTargetCards.isEmpty()) {
                final Set<Integer> allowedCardIds = new HashSet<>();
                for (final Card card : mustTargetCards) {
                    allowedCardIds.add(card.getId());
                }
                candidates.removeIf(candidate -> !(candidate instanceof Card)
                        || !allowedCardIds.contains(candidate.getId()));
            }
            if (candidates.isEmpty()) {
                return false;
            }

            final FCollection<GameEntity> authoritative = new FCollection<>();
            authoritative.addAll(candidates);
            final List<GameEntity> selected = chooseExternalEntities(
                    authoritative, 1, 1, false, currentAbility, "TARGET_SELECTION");
            if (selected.size() != 1) {
                return false;
            }
            return currentAbility.getTargets().add(selected.get(0));
        }
        final TargetSelection select = new TargetSelection(this, currentAbility);
'''
    text = once(text, old, new, "chooseTargetsFor strict boundary")
    p.write_text(text, encoding="utf-8")
    print("WS31_SINGLE_TARGET_DECISION_OVERLAY_APPLIED=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
