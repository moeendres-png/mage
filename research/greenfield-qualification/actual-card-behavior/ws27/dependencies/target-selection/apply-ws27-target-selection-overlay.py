#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("forge_root", type=Path)
    ns = ap.parse_args()

    pch = ns.forge_root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    target = ns.forge_root / "forge-gui/src/main/java/forge/player/TargetSelection.java"

    pch_text = pch.read_text(encoding="utf-8")
    pch_text = replace_once(
        pch_text,
        '        rejectExternalDecision("TARGET_SELECTION");',
        '        if (hasExternalDecisionProvider()) {\n'
        '            return new TargetSelection(this, currentAbility).chooseExternalTargets();\n'
        '        }',
        "PlayerControllerHuman TARGET_SELECTION boundary",
    )
    pch.write_text(pch_text, encoding="utf-8")

    target_text = target.read_text(encoding="utf-8")
    target_text = replace_once(
        target_text,
        "import forge.gamemodes.match.input.InputSelectTargets;",
        "import forge.gamemodes.match.input.InputSelectTargets;\n"
        "import forge.gamemodes.match.input.ExternalDecisionRequest;\n"
        "import forge.gamemodes.match.input.ExternalDecisionValidationException;",
        "TargetSelection imports",
    )

    marker = "    private boolean chooseCardFromList(final List<Card> choices, final boolean targeted, final boolean mandatory) {"
    method = r'''    /**
     * Strict external single-target adapter.
     *
     * The option list is computed only from Forge's TargetRestrictions,
     * CardUtil and StaticAbilityMustTarget rules. The external pilot receives
     * that authoritative set and may select only a validated member. Complex
     * target topologies remain fail-closed until separately qualified.
     */
    public final boolean chooseExternalTargets() {
        if (!controller.hasExternalDecisionProvider()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "external target selection requires an installed provider");
        }
        if (!ability.usesTargeting() || getTgt() == null) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "TARGET_SELECTION invoked without TargetRestrictions");
        }

        final TargetRestrictions tgt = getTgt();
        if (tgt.getZone().contains(ZoneType.Stack)) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "stack targeting needs a dedicated typed adapter");
        }
        if (ability.isDividedAsYouChoose()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "divided target allocation needs a dedicated typed adapter");
        }

        // Random targets are rules-owned, not discretionary pilot choices. Reuse
        // the existing Forge random-target branch, which returns before any GUI.
        if (tgt.isRandomTarget()) {
            return chooseTargets(null, null, null, false, true);
        }

        final int minTargets = ability.getMinTargets();
        final int maxTargets = ability.getMaxTargets();
        final int alreadyTargeted = ability.getTargets().size();
        final int remainingMax = Math.max(0, maxTargets - alreadyTargeted);
        if (remainingMax == 0) {
            return ability.isTargetNumberValid();
        }
        if (remainingMax > 1) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "multi-target combination semantics are not qualified by the single-target adapter");
        }

        List<GameEntity> candidates = new ArrayList<>(tgt.getAllCandidates(ability));
        final List<Card> validCardTargets = CardUtil.getValidCardsToTarget(ability);
        final boolean mustTargetFiltered = StaticAbilityMustTarget.filterMustTargetCards(
                controller.getPlayer(), validCardTargets, ability);
        if (mustTargetFiltered) {
            candidates = new ArrayList<>(validCardTargets);
        }

        final int remainingMin = Math.max(0, minTargets - alreadyTargeted);
        if (candidates.size() < remainingMin) {
            return false;
        }
        if (candidates.isEmpty()) {
            return remainingMin == 0;
        }

        final int maxSelect = Math.min(remainingMax, candidates.size());
        final boolean cancelAllowed = !ability.isTrigger();
        final List<GameEntity> selected = controller.chooseExternalUiOptions(
                candidates, remainingMin, maxSelect, cancelAllowed, false,
                "TARGET_SELECTION", ExternalDecisionRequest::optionIdFor);

        if (selected.isEmpty()) {
            return remainingMin == 0;
        }
        if (!ability.getTargets().addAll(selected)) {
            return false;
        }
        return ability.isTargetNumberValid();
    }

'''
    target_text = replace_once(target_text, marker, method + marker, "TargetSelection external adapter insertion")
    target.write_text(target_text, encoding="utf-8")

    print("WS27_TARGET_SELECTION_OVERLAY_APPLIED=TRUE")
    print("WS27_TARGET_SELECTION_COMPLEX_PATHS_FAIL_CLOSED=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
