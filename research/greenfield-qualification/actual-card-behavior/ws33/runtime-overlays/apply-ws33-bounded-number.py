#!/usr/bin/env python3
"""Externalize authoritative finite integer choices without GUI fallback."""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exact anchor once, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--forge-root", type=Path, required=True)
    args = parser.parse_args()
    source = args.forge_root.resolve() / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
    text = source.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "import forge.ai.AIOption;\n",
        "import forge.ai.AIOption;\nimport forge.ai.ComputerUtilMana;\n",
        "mana feasibility import",
    )

    for old in (
        '            return getGui().getInteger(localizer.getMessage("lblHowManyTimesToPay", ability.getPayCosts().getTotalMana(),\n'
        '                    host.getTranslatedName()), min, max, min + 9);\n',
        '        return getGui().getInteger(localizer.getMessage("lblChooseAnnounceForCard", announceTitle,\n'
        '                host.getTranslatedName()), min, max, min + 9);\n',
    ):
        new = old.replace('return getGui().getInteger', 'if (hasExternalDecisionProvider()) {\n                return chooseNumber(ability,')
        if old.startswith('            '):
            new = ('            if (hasExternalDecisionProvider()) {\n'
                   '                return chooseNumber(ability, localizer.getMessage("lblHowManyTimesToPay", ability.getPayCosts().getTotalMana(),\n'
                   '                        host.getTranslatedName()), min, max);\n'
                   '            }\n' + old)
            text = replace_once(text, old, new, "NumTimes bounded number externalization")
        else:
            new = ('        if (hasExternalDecisionProvider()) {\n'
                   '            if ("X".equals(announce) && max == Integer.MAX_VALUE) {\n'
                   '                return chooseExternalDiscrete(externalLegalXManaChoices(ability, min), 1, 1, false, false,\n'
                   '                        "NUMBER_ENUM", String::valueOf).get(0);\n'
                   '            }\n'
                   '            return chooseNumber(ability, localizer.getMessage("lblChooseAnnounceForCard", announceTitle,\n'
                   '                    host.getTranslatedName()), min, max);\n'
                   '        }\n' + old)
            text = replace_once(text, old, new, "announce bounded number externalization")

    helper_anchor = '    @Override\n    public CardCollectionView choosePermanentsToSacrifice('
    helper = '''    private List<Integer> externalLegalXManaChoices(final SpellAbility ability, final int min) {
        final Cost cost = ability.getPayCosts();
        if (cost == null || !cost.hasManaCost() || cost.getCostMana().getAmountOfX() < 1) {
            throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "unbounded external X announcement has no mana-X feasibility contract");
        }
        long potentialMana = player.getManaPool().totalMana();
        for (final Card source : player.getCardsIn(ZoneType.Battlefield)) {
            potentialMana += Math.max(0, source.getMaxManaProduced());
            if (potentialMana > 10000L) {
                throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "external mana-X legal domain exceeds exact option-set limit");
            }
        }
        final int upper = (int) potentialMana;
        final List<Integer> legal = new ArrayList<>();
        for (int value = min; value <= upper; value++) {
            if (ComputerUtilMana.canPayManaCost(cost, ability, player, value, false)) {
                legal.add(value);
            }
        }
        if (legal.isEmpty()) {
            throw new ExternalDecisionValidationException(ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "authoritative mana payment has no legal X value");
        }
        return legal;
    }

'''
    text = replace_once(text, helper_anchor, helper + helper_anchor, "external mana-X feasibility helper")

    source.write_text(text, encoding="utf-8")
    print("WS33_BOUNDED_NUMBER_EXTERNALIZED=PASS finite_range=true x_mana_feasibility=true gui_fallback_external_mode=0 rules_mutation=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
