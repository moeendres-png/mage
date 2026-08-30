#!/usr/bin/env python3
"""WS31 qualification-only harness patch.

Applies narrowly audited changes to the copied WS31 Forge test source after the
WS01/WS05/WS06 overlays are applied. This file never changes production Forge;
it only removes a desktop reveal acknowledgement from the headless witness and
routes the exact effect through Forge's MagicStack instead of SpellAbility.resolve.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {n}")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("java_file", type=Path)
    ns = ap.parse_args()
    p = ns.java_file
    text = p.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "import forge.model.FModel;",
        "import forge.model.FModel;\nimport forge.localinstance.properties.ForgePreferences.FPref;",
        "FPref import",
    )

    text = replace_once(
        text,
        "TestUtils.ensureFModelInitialized();",
        "TestUtils.ensureFModelInitialized();FModel.getPreferences().setPref(FPref.UI_SELECT_FROM_CARD_DISPLAYS,\"false\");",
        "headless reveal preference",
    )

    old = (
        "bindTarget(sa,game,actor,opponent);ce.beforeState=semanticState(game);"
        "ce.beforeDigest=sha256(ce.beforeState);sa.resolve();game.getAction().checkStateEffects(true);"
    )
    new = (
        "bindTarget(sa,game,actor,opponent);ce.beforeState=semanticState(game);"
        "ce.beforeDigest=sha256(ce.beforeState);game.getStack().add(sa);game.getStack().resolveStack();"
        "game.getAction().checkStateEffects(true);game.getStack().addAllTriggeredAbilitiesToStack();"
        "while(!game.getStack().isEmpty()){game.getStack().resolveStack();game.getAction().checkStateEffects(true);"
        "game.getStack().addAllTriggeredAbilitiesToStack();}"
    )
    text = replace_once(text, old, new, "MagicStack resolution path")

    p.write_text(text, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
