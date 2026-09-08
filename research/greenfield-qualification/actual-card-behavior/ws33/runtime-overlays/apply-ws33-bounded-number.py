#!/usr/bin/env python3
"""Externalize finite authoritative integer ranges without altering Forge rules."""
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
                   '            return chooseNumber(ability, localizer.getMessage("lblChooseAnnounceForCard", announceTitle,\n'
                   '                    host.getTranslatedName()), min, max);\n'
                   '        }\n' + old)
            text = replace_once(text, old, new, "announce bounded number externalization")

    source.write_text(text, encoding="utf-8")
    print("WS33_BOUNDED_NUMBER_EXTERNALIZED=PASS finite_range=true gui_fallback_external_mode=0 rules_mutation=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
