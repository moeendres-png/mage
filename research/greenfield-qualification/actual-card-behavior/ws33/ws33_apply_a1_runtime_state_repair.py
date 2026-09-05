#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_A1_RUNTIME_STATE_REPAIR=FAIL " + message)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    require(count == 1, f"{label} anchor count={count}")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=Path, required=True)
    args = parser.parse_args()
    require(args.test.is_file(), f"missing test {args.test}")
    text = args.test.read_text(encoding="utf-8")

    text = replace_once(
        text,
        "import forge.game.ability.AbilityFactory;\n",
        "import forge.game.ability.AbilityFactory;\nimport forge.game.ability.AbilityUtils;\n",
        "AbilityUtils import",
    )
    text = replace_once(
        text,
        "import org.testng.Assert;\n",
        "import org.apache.commons.lang3.Range;\nimport org.testng.Assert;\n",
        "Range import",
    )

    old = '''        if (c.validTgts.contains("TriggeredDefendingPlayer")) {
            ability.setTriggeringObject(AbilityKey.DefendingPlayer, opponent);
        }
        if ("TriggeredCardController".equals(ability.getParam("TargetsWithDefinedController"))) {
            ability.setTriggeringObject(AbilityKey.Card, source);
        }
'''
    new = '''        final String targetsWithDefinedController = ability.getParam("TargetsWithDefinedController");
        if ("TriggeredDefendingPlayer".equals(targetsWithDefinedController)
                || c.validTgts.contains("TriggeredDefendingPlayer")) {
            ability.setTriggeringObject(AbilityKey.DefendingPlayer, opponent);
        }
        if ("TriggeredCardController".equals(targetsWithDefinedController)) {
            ability.setTriggeringObject(AbilityKey.Card, source);
        }
'''
    text = replace_once(text, old, new, "parameter-driven defined-controller context")

    old = '''            case "OPPONENT_CREATURE":
                intended = addCardToZone("Runeclaw Bear", opponent,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                if ("GRAVEYARD".equals(c.fixtureContext)) {
                    addCardToZone("Runeclaw Bear", opponent, ZoneType.Graveyard);
                }
                relation = "OPPONENT";
                break;
'''
    new = '''            case "OPPONENT_CREATURE": {
                // A selector-only campaign role may be narrower than the actual
                // ability's TargetsWithDefinedController contract. Derive the
                // fixture controller from that Forge parameter, never from a
                // card-name exception, and still require Forge to emit the
                // resulting card as an authoritative legal option.
                final Player fixtureController = "TriggeredCardController".equals(targetsWithDefinedController)
                        ? source.getController() : opponent;
                intended = addCardToZone("Runeclaw Bear", fixtureController,
                        "GRAVEYARD".equals(c.fixtureContext) ? ZoneType.Graveyard : ZoneType.Battlefield);
                if ("GRAVEYARD".equals(c.fixtureContext)) {
                    addCardToZone("Runeclaw Bear", fixtureController, ZoneType.Graveyard);
                }
                relation = fixtureController == actor ? "ACTOR" : "OPPONENT";
                break;
            }
'''
    text = replace_once(text, old, new, "defined-controller creature fixture")

    old = '''        final int initialTargetCount = ability.getTargets().size();
        if (initialTargetCount != 0) {
            throw new IllegalStateException("actual ability already has targets before qualification");
        }
        final TargetRestrictions authoritativeRestrictions = ability.getTargetRestrictions();
'''
    new = '''        final int initialTargetCount = ability.getTargets().size();
        if (initialTargetCount != 0) {
            throw new IllegalStateException("actual ability already has targets before qualification");
        }

        // Reproduce Forge's production target-reset lifecycle. clearTargets()
        // is where pinned Forge initializes DividedAsYouChoose from the actual
        // card parameters. A direct chooseTargetsFor() call without this step
        // enters TargetSelection with dividedValue == null and can legitimately
        // terminate before opening a target decision.
        final Integer qualificationX = establishTargetRelevantPaidXState(ability);
        ability.clearTargets();
        if (!ability.getTargets().isEmpty()) {
            throw new IllegalStateException("Forge target reset retained unexpected targets");
        }
        if (ability.isDividedAsYouChoose() && ability.getDividedValue() == null) {
            throw new IllegalStateException("Forge did not initialize divided target state");
        }

        final TargetRestrictions authoritativeRestrictions = ability.getTargetRestrictions();
'''
    text = replace_once(text, old, new, "production target lifecycle initialization")

    marker = '''    private List<GameObject> provisionQualificationFillers(
'''
    helper = '''    private int establishTargetRelevantPaidXState(final SpellAbility ability) {
        final boolean countXPaid = "Count$xPaid".equals(ability.getSVar("X"));
        final boolean targetMinUsesX = ability.hasParam("TargetMin") && "X".equals(ability.getParam("TargetMin"));
        final boolean targetMaxUsesX = ability.hasParam("TargetMax") && "X".equals(ability.getParam("TargetMax"));
        final boolean dividedUsesX = ability.hasParam("DividedAsYouChoose")
                && "X".equals(ability.getParam("DividedAsYouChoose"));
        if (!countXPaid || !(targetMinUsesX || targetMaxUsesX || dividedUsesX)) {
            return -1;
        }

        // This A1 shard qualifies TargetRestrictions, not CostPayment. Establish
        // an already-paid X=1 prerequisite state only after Forge itself proves
        // that 1 lies inside the production announcement bounds. The value is
        // then consumed by the card's real Count$xPaid SVar and by Forge's own
        // TargetRestrictions/DividedAsYouChoose calculations. No target count,
        // legal option, or effect outcome is injected by the harness.
        final Range<Integer> bounds = AbilityUtils.getAnnouncementBounds(ability, "X");
        if (!bounds.contains(1)) {
            throw new IllegalStateException("A1 paid-X prerequisite cannot establish X=1 inside Forge bounds " + bounds);
        }
        ability.setXManaCostPaid(1);
        if (!Integer.valueOf(1).equals(ability.getXManaCostPaid())) {
            throw new IllegalStateException("Forge did not retain paid-X prerequisite state");
        }
        return 1;
    }

'''
    text = replace_once(text, marker, helper + marker, "paid-X prerequisite helper")

    old = '''        final String canonical = "target_count=" + finalTargetCount
                + "|target_min=" + authoritativeMinTargets
'''
    new = '''        final String canonical = "target_count=" + finalTargetCount
                + "|qualification_x=" + qualificationX
                + "|target_min=" + authoritativeMinTargets
'''
    text = replace_once(text, old, new, "canonical paid-X state")

    args.test.write_text(text, encoding="utf-8")
    print("WS33_A1_RUNTIME_STATE_REPAIR=PASS")
    print("WS33_A1_TARGET_RESET_LIFECYCLE=FORGE_CLEAR_TARGETS")
    print("WS33_A1_DEFINED_CONTROLLER_CONTEXT=ABILITY_PARAMETER_DRIVEN")
    print("WS33_A1_PAID_X_PREREQUISITE=FORGE_BOUNDED_X1")
    print("WS33_A1_TARGET_LEGALITY_AUTHORITY=FORGE")
    print("WS33_A1_CARD_NAME_PRODUCTION_BRANCHES=0")
    print("WS33_A1_RULES_MUTATION=FALSE")


if __name__ == "__main__":
    main()
