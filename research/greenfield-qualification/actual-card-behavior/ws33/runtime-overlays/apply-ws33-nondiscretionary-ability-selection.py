#!/usr/bin/env python3
"""Restore pinned Forge's non-discretionary singleton ability-selection behavior.

PlaySpellAbility.chooseOptionalAdditionalCosts calls PlayerController.getAbilityToPlay even
when GameActionUtil.getAdditionalCostSpell returned exactly one authoritative variant.
Pinned Desktop Forge's no-trigger-event GUI path returns that singleton directly; strict
external mode must not turn the same non-choice into an unsupported pilot decision.

This overlay selects only when the authoritative list size is exactly one. Empty and
multi-option lists retain the pinned controller path unchanged. It does not infer legality,
choose among alternatives, mutate costs/targets, or add a fallback.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_NONDISCRETIONARY_ABILITY_SELECTION=FAIL {label}: expected one match, got {count}")
    return text.replace(old, new, 1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()

    path = args.forge_root / "forge-game/src/main/java/forge/game/player/PlaySpellAbility.java"
    src = path.read_text(encoding="utf-8")

    anchor = """        // choose alternative additional cost
        final List<SpellAbility> abilities = GameActionUtil.getAdditionalCostSpell(original);

        final SpellAbility choosen = c.getAbilityToPlay(original.getHostCard(), abilities);

        List<OptionalCostValue> list = GameActionUtil.getOptionalCostValues(choosen);
"""
    replacement = """        // choose alternative additional cost
        final List<SpellAbility> abilities = GameActionUtil.getAdditionalCostSpell(original);

        // The pinned desktop no-trigger-event path returns the sole authoritative
        // variant directly. A singleton is not a discretionary pilot decision.
        // Preserve the existing controller path for zero or multiple variants.
        final SpellAbility choosen = abilities.size() == 1
                ? abilities.get(0)
                : c.getAbilityToPlay(original.getHostCard(), abilities);

        List<OptionalCostValue> list = GameActionUtil.getOptionalCostValues(choosen);
"""
    src = replace_once(src, anchor, replacement, "PlaySpellAbility singleton selection anchor")

    required = (
        "final SpellAbility choosen = abilities.size() == 1",
        "? abilities.get(0)",
        ": c.getAbilityToPlay(original.getHostCard(), abilities);",
        "GameActionUtil.getOptionalCostValues(choosen)",
    )
    for token in required:
        if token not in src:
            raise SystemExit(f"WS33_NONDISCRETIONARY_ABILITY_SELECTION=FAIL missing {token}")

    forbidden = (
        "abilities.get(0); // fallback",
        "abilities.isEmpty() ?",
        "Math.min(1, abilities.size())",
    )
    for token in forbidden:
        if token in src:
            raise SystemExit(f"WS33_NONDISCRETIONARY_ABILITY_SELECTION=FAIL forbidden fallback token {token}")

    path.write_text(src, encoding="utf-8")
    print("WS33_NONDISCRETIONARY_ABILITY_SELECTION=PASS authoritative_singleton_only=true multi_option_auto_select=false rules_mutation=false")


if __name__ == "__main__":
    main()
