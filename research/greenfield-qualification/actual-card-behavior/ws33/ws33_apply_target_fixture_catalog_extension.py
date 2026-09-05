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

    # Complete A1 materialization closure inventory (50 path occurrences,
    # 49 additional selector strings; Creature.cmcLEX has two actual paths).
    "Permanent.Black,Permanent.Red": "OPPONENT_BLACK_CREATURE",
    "Creature.White,Creature.Blue": "OPPONENT_WHITE_CREATURE",
    "Creature.ControlledBy TriggeredDefendingPlayer": "OPPONENT_CREATURE",
    "Creature.YouOwn+ThisTurnEnteredFrom_Battlefield": "OWN_THIS_TURN_FROM_BATTLEFIELD_CREATURE",
    "Creature.nonVampire+nonWerewolf+nonZombie": "OPPONENT_CREATURE",
    "Creature.nonLegendary+YouOwn": "OWN_CREATURE",
    "Card.ExiledWithSource": "OWN_EXILED_WITH_SOURCE_CARD",
    "Creature.YouCtrl+cmcLE3": "OWN_CREATURE",
    "Creature.Legendary+YouCtrl": "OWN_LEGENDARY_PERMANENT",
    "Permanent.YouCtrl+cmcLE4": "OWN_CREATURE",
    "Artifact.YouCtrl+cmcEQX+!token": "OWN_ZERO_CMC_ARTIFACT",
    "Aura.YouOwn,Equipment.YouOwn": "OWN_AURA",
    "Permanent.OppCtrl+cmcGE3": "OPPONENT_ELEMENTAL",
    "Creature.tapped": "OPPONENT_TAPPED_CREATURE",
    "Creature.nonLegendary+YouCtrl": "OWN_CREATURE",
    "Creature.MultiColor": "OPPONENT_MULTICOLOR_CREATURE",
    "Creature.powerGE4": "OPPONENT_POWER4_CREATURE",
    "Creature.HasCounters": "OWN_COUNTER_CREATURE",
    "Creature.cmcLEX+YouCtrl": "OWN_ZERO_CMC_NONBEAR_CREATURE",
    "Creature.cmcLEX": "OPPONENT_ZERO_CMC_CREATURE",
    "Creature.attacking+YouCtrl,Creature.blocking+YouCtrl": "OWN_ATTACKING_CREATURE",
    "Creature.ControlledBy ParentTargetedController,Creature.ControlledBy ParentTarget": "OPPONENT_CREATURE",
    "Instant.YouCtrl+cmcLEX,Sorcery.YouCtrl+cmcLEX": "OWN_INSTANT",
    "Creature.OppOwn": "OPPONENT_CREATURE",
    "Creature.OppCtrl,Enchantment.OppCtrl": "OPPONENT_CREATURE",
    "Creature.ControlledBy TriggeredTarget": "OPPONENT_CREATURE",
    "Permanent.nonLand+cmcLEX+YouOwn": "OWN_ZERO_CMC_NONBEAR_CREATURE",
    "Creature.Green,Creature.White": "OPPONENT_WHITE_CREATURE",
    "Creature.Assembly-Worker": "OPPONENT_ASSEMBLY_WORKER",
    "Artifact.YouOwn+cmcLE3,Creature.YouOwn+cmcLE3,Enchantment.nonAura+YouOwn+cmcLE3": "OWN_ARTIFACT",
    "Creature.cmcLE2": "OPPONENT_CREATURE",
    "Permanent.nonLand+tapped+ControlledBy TriggeredDefendingPlayer": "OPPONENT_TAPPED_CREATURE",
    "Card.nonCreature+nonLand+YouOwn": "OWN_ARTIFACT",
    "Permanent.nonLand+!token+YouDontCtrl+cmcLE4": "OPPONENT_CREATURE",
    "Vampire.YouCtrl": "OWN_VAMPIRE",
    "Creature.nonWhite": "OPPONENT_BLACK_CREATURE",
    "Permanent.nonLand+nonCreature+ControlledBy TriggeredTarget": "OPPONENT_ARTIFACT",
    "Permanent.MonoColor": "OPPONENT_BLACK_CREATURE",
    "Ninja,Turtle": "OPPONENT_NINJA",
    "Card.Red,Card.Green": "OPPONENT_CREATURE",
    "Creature.OppCtrl,Planeswalker.OppCtrl": "OPPONENT_CREATURE",
    "Creature.attacking+withoutFlying": "OPPONENT_ATTACKING_CREATURE",
    "Enchantment,Instant,Sorcery": "OPPONENT_INSTANT",
    "Card.cmcLE3": "OPPONENT_INSTANT",
    "Any.NotDefinedParentTarget,Player": "OPPONENT_PLAYER",
    "Creature.YouOwn+cmcLEX": "OWN_ZERO_CMC_NONBEAR_CREATURE",
    "Creature.Legendary": "OPPONENT_WHITE_CREATURE",
    "Creature.counters_GE1_M1M1": "OPPONENT_M1M1_COUNTER_CREATURE",
    "Artifact.YouOwn,Creature.YouOwn": "OWN_ARTIFACT",
}
def load(path: Path):'''
    text = replace_once(text, anchor, replacement, "preparer selector map")
    path.write_text(text, encoding="utf-8")


def patch_test(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = replace_once(
        text,
        "import forge.game.GameObject;\n",
        "import forge.game.GameObject;\nimport forge.game.combat.Combat;\nimport forge.game.card.CounterEnumType;\nimport forge.game.spellability.AbilitySub;\n",
        "fixture imports",
    )
    text = replace_once(
        text,
        '''        if ("TriggeredTarget".equals(ability.getParam("TargetsWithDefinedController"))) {
            ability.setTriggeringObject(AbilityKey.Target, opponent);
        }
''',
        '''        if ("TriggeredTarget".equals(ability.getParam("TargetsWithDefinedController"))
                || c.validTgts.contains("TriggeredTarget")) {
            ability.setTriggeringObject(AbilityKey.Target, opponent);
        }
        if (c.validTgts.contains("TriggeredDefendingPlayer")) {
            ability.setTriggeringObject(AbilityKey.DefendingPlayer, opponent);
        }
        if (c.validTgts.contains("ParentTargetedController") || c.validTgts.contains("ParentTarget")) {
            if (!(ability instanceof AbilitySub)) {
                throw new IllegalStateException("parent-dependent selector did not materialize as AbilitySub");
            }
            final SpellAbility parent = source.getSpells().get(0);
            parent.setActivatingPlayer(actor);
            parent.getTargets().add(opponent);
            ((AbilitySub) ability).setParent(parent);
        }
''',
        "trigger/parent selector context",
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
            case "OWN_ATTACKING_CREATURE": {
                final Card attacker = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                final Combat combat = new Combat(actor);
                game.getPhaseHandler().setCombat(combat);
                combat.addAttacker(attacker, opponent);
                if (!combat.getAttackers().contains(attacker)) {
                    throw new IllegalStateException("own combat attacker fixture was not retained by Forge Combat");
                }
                intended = attacker;
                relation = "ACTOR";
                break;
            }
            case "OPPONENT_POWER4_CREATURE":
                intended = addCardToZone("Air Elemental", opponent, ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_COUNTER_CREATURE": {
                final Card countered = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                countered.addCounterInternal(CounterEnumType.P1P1, 1, actor, false, null, null);
                intended = countered;
                relation = "ACTOR";
                break;
            }
            case "OPPONENT_M1M1_COUNTER_CREATURE": {
                final Card countered = addCardToZone("Runeclaw Bear", opponent, ZoneType.Battlefield);
                countered.addCounterInternal(CounterEnumType.M1M1, 1, actor, false, null, null);
                intended = countered;
                relation = "OPPONENT";
                break;
            }
            case "OWN_ZERO_CMC_NONBEAR_CREATURE":
                intended = addCardToZone("Ornithopter", actor,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "ACTOR";
                break;
            case "OPPONENT_ZERO_CMC_CREATURE":
                intended = addCardToZone("Ornithopter", opponent,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_ZERO_CMC_ARTIFACT":
                intended = addCardToZone("Ornithopter", actor, ZoneType.Battlefield);
                relation = "ACTOR";
                break;
            case "OPPONENT_BLACK_CREATURE":
                intended = addCardToZone("Walking Corpse", opponent, ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_LEGENDARY_PERMANENT":
                intended = addCardToZone("Isamaru, Hound of Konda", actor,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "ACTOR";
                break;
            case "OPPONENT_WHITE_CREATURE":
                intended = addCardToZone("Isamaru, Hound of Konda", opponent,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_AURA":
                intended = addCardToZone("Pacifism", actor,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                relation = "ACTOR";
                break;
            case "OPPONENT_MULTICOLOR_CREATURE":
                intended = addCardToZone("Fusion Elemental", opponent, ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OPPONENT_ASSEMBLY_WORKER":
                intended = addCardToZone("Assembly-Worker", opponent, ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OWN_VAMPIRE":
                intended = addCardToZone("Vampire Nighthawk", actor, ZoneType.Battlefield);
                relation = "ACTOR";
                break;
            case "OPPONENT_NINJA":
                intended = addCardToZone("Ninja of the Deep Hours", opponent, ZoneType.Battlefield);
                relation = "OPPONENT";
                break;
            case "OPPONENT_TAPPED_CREATURE": {
                final Card tapped = addCardToZone("Runeclaw Bear", opponent, ZoneType.Battlefield);
                tapped.setTapped(true);
                intended = tapped;
                relation = "OPPONENT";
                break;
            }
            case "OWN_THIS_TURN_FROM_BATTLEFIELD_CREATURE": {
                final Card moved = addCardToZone("Runeclaw Bear", actor, ZoneType.Battlefield);
                final Card graveCard = game.getAction().moveTo(ZoneType.Graveyard, moved, null, null);
                if (graveCard == null || graveCard.getZone() == null || graveCard.getZone().getZoneType() != ZoneType.Graveyard) {
                    throw new IllegalStateException("battlefield-to-graveyard fixture move failed");
                }
                intended = graveCard;
                relation = "ACTOR";
                break;
            }
            case "OWN_EXILED_WITH_SOURCE_CARD": {
                final Card exiled = addCardToZone("Shock", actor, ZoneType.Exile);
                source.addExiledCard(exiled);
                exiled.setExiledWith(source);
                exiled.setExiledBy(actor);
                intended = exiled;
                relation = "ACTOR";
                break;
            }
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
    print("WS33_TARGET_FIXTURE_EXTENSION_SELECTOR_SHAPES=64")
    print("WS33_TARGET_FIXTURE_EXTENSION_A1_MISSING_OCCURRENCES_CLOSED=50")
    print("WS33_TARGET_FIXTURE_EXTENSION_RULES_MUTATION=FALSE")
    print("WS33_TARGET_FIXTURE_EXTENSION_CARD_NAME_PRODUCTION_BRANCHES=0")


if __name__ == "__main__":
    main()
