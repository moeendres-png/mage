#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_TARGET_FIXTURE_EXTENSION=FAIL " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label} anchor count={count}")
    return text.replace(old, new, 1)


def patch_preparer(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    anchor = '    "Permanent.nonLand+YouCtrl": "OWN_CREATURE",\n}\ndef load(path: Path):'
    replacement = '''    "Permanent.nonLand+YouCtrl": "OWN_CREATURE",
    # ABC-A1 generic fixture catalog extensions. These are selector-shape
    # mappings only; Forge remains the authority that must emit the target as
    # legal at runtime before the external pilot may choose it.
    "Villain.YouCtrl": "OWN_SOURCE",
    "Creature.withHaste": "OWN_SOURCE",
    "Creature.attacking": "OPPONENT_ATTACKING_CREATURE",
    "Creature.attacking,Creature.blocking": "OPPONENT_ATTACKING_CREATURE",
    "Creature.powerGE4,Artifact,Enchantment": "OPPONENT_POWER4_CREATURE",
    "Artifact.cmcLE2+YouOwn,Creature.cmcLE2+YouOwn": "OWN_ARTIFACT",
    "Card.!wasCastFromTheirHand": "OPPONENT_NONHAND_SPELL",
    "Creature.withFlying": "OPPONENT_ELEMENTAL",
    "Creature.YouCtrl+HasCounters": "OWN_COUNTER_CREATURE",
    "Creature.cmcLEX+YouOwn+nonBear+Other": "OWN_ZERO_CMC_NONBEAR_CREATURE",
    "Creature.YouCtrl+cmcLEX": "OWN_ZERO_CMC_NONBEAR_CREATURE",
    "Creature.Black,Planeswalker.Red,Creature.Red,Planeswalker.Black": "OPPONENT_BLACK_CREATURE",
    "Permanent.cmcLE3+YouCtrl": "OWN_ARTIFACT",
    "Permanent.Legendary+Other+YouCtrl": "OWN_LEGENDARY_PERMANENT",
    "Creature.White": "OPPONENT_WHITE_CREATURE",
}
def load(path: Path):'''
    text = replace_once(text, anchor, replacement, "preparer selector map")
    path.write_text(text, encoding="utf-8")


def patch_test(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import forge.game.GameObject;\n",
        "import forge.game.GameObject;\nimport forge.game.combat.Combat;\nimport forge.game.card.CounterEnumType;\n",
        "Combat/counter imports",
    )
    text = replace_once(
        text,
        '''            stackOwner.getZone(ZoneType.Hand).add(stackTarget);
            final SpellAbility stackAbility = stackTarget.getSpells().get(0);
''',
        '''            final ZoneType stackOrigin = "OPPONENT_NONHAND_SPELL".equals(c.targetRole)
                    ? ZoneType.Graveyard : ZoneType.Hand;
            stackOwner.getZone(stackOrigin).add(stackTarget);
            final SpellAbility stackAbility = stackTarget.getSpells().get(0);
''',
        "non-hand stack origin",
    )
    anchor = '''        } else switch (c.targetRole) {
            case "OPPONENT_PLAYER":
'''
    replacement = '''        } else switch (c.targetRole) {
            case "OWN_SOURCE":
                intended = source;
                relation = "ACTOR";
                break;
            case "OPPONENT_ATTACKING_CREATURE": {
                final Card attacker = addCardToZone("Runeclaw Bear", opponent, ZoneType.Battlefield);
                final Combat combat = new Combat(opponent);
                game.getPhaseHandler().setCombat(combat);
                combat.addAttacker(attacker, actor);
                if (!combat.getAttackers().contains(attacker)) {
                    throw new IllegalStateException("combat attacker fixture was not retained by Forge Combat");
                }
                intended = attacker;
                relation = "OPPONENT";
                break;
            }
            case "OPPONENT_POWER4_CREATURE":
                intended = addCardToZone("Air Elemental", opponent, ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_COUNTER_CREATURE": {
                final Card countered = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                countered.addCounterInternal(CounterEnumType.P1P1, 1, actor, false, null, null);
                if (countered.getCounters(CounterEnumType.P1P1) != 1) {
                    throw new IllegalStateException("counter fixture was not retained by Forge Card state");
                }
                intended = countered;
                relation = "ACTOR";
                break;
            }
            case "OWN_ZERO_CMC_NONBEAR_CREATURE":
                intended = addCardToZone("Ornithopter", actor, ZoneType.Graveyard);
                relation = "ACTOR";
                break;
            case "OPPONENT_BLACK_CREATURE":
                intended = addCardToZone("Walking Corpse", opponent, ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_LEGENDARY_PERMANENT":
                intended = addCardToZone("Isamaru, Hound of Konda", actor, ZoneType.Battlefield);
                relation = "ACTOR";
                break;
            case "OPPONENT_WHITE_CREATURE":
                intended = addCardToZone("Isamaru, Hound of Konda", opponent, ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OPPONENT_PLAYER":
'''
    text = replace_once(text, anchor, replacement, "target role switch")
    path.write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preparer", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    args = parser.parse_args()
    require(args.preparer.is_file(), f"missing preparer {args.preparer}")
    require(args.test.is_file(), f"missing test {args.test}")
    patch_preparer(args.preparer)
    patch_test(args.test)
    print("WS33_TARGET_FIXTURE_EXTENSION=PASS")
    print("WS33_TARGET_FIXTURE_EXTENSION_SELECTOR_SHAPES=15")
    print("WS33_TARGET_FIXTURE_EXTENSION_RULES_MUTATION=FALSE")
    print("WS33_TARGET_FIXTURE_EXTENSION_CARD_NAME_PRODUCTION_BRANCHES=0")


if __name__ == "__main__":
    main()
