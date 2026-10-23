package org.mage.test.cards.single.blc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Zinnia, Valley's Voice {U}{R}{W} 1/3
 * Flying
 * Zinnia gets +X/+0, where X is the number of other creatures you control with base power 1.
 * Creature spells you cast gain offspring {2} as you cast them.
 */
public class ZinniaValleysVoiceTest extends CardTestPlayerBase {

    private static final String zinnia = "Zinnia, Valley's Voice";
    private static final String elves = "Llanowar Elves"; // 1/1
    private static final String bears = "Grizzly Bears"; // 2/2

    @Test
    public void testBoostCountsOtherCreaturesWithBasePowerOne() {
        addCard(Zone.BATTLEFIELD, playerA, zinnia);
        addCard(Zone.BATTLEFIELD, playerA, elves, 2);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        // a creature with base power 1 that is pumped still has base power 1
        addCard(Zone.HAND, playerA, "Giant Growth");
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        // an opponent's creature with base power 1 does not count
        addCard(Zone.BATTLEFIELD, playerB, elves);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Giant Growth", elves + "^");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // 1 base + two other creatures with base power 1 (the Bears and Zinnia herself do not count)
        assertPowerToughness(playerA, zinnia, 3, 3);
    }

    @Test
    public void testNoBoostWithoutOtherSmallCreatures() {
        addCard(Zone.BATTLEFIELD, playerA, zinnia);
        addCard(Zone.BATTLEFIELD, playerA, bears);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPowerToughness(playerA, zinnia, 1, 3);
    }

    @Test
    public void testCreatureSpellGainsOffspring() {
        addCard(Zone.BATTLEFIELD, playerA, zinnia);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 4);
        addCard(Zone.HAND, playerA, bears);

        // {1}{G} plus the offspring cost {2}
        setChoice(playerA, true);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, bears);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, bears, 2);
        assertTokenCount(playerA, bears, 1);
        // the 1/1 token copy of the Bears has base power 1, so Zinnia gets +1/+0
        assertPowerToughness(playerA, zinnia, 2, 3);
    }

    @Test
    public void testOffspringIsOptional() {
        addCard(Zone.BATTLEFIELD, playerA, zinnia);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 4);
        addCard(Zone.HAND, playerA, bears);

        setChoice(playerA, false);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, bears);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, bears, 1);
        assertTokenCount(playerA, bears, 0);
    }

    @Test
    public void testNoncreatureSpellDoesNotAskForOffspring() {
        addCard(Zone.BATTLEFIELD, playerA, zinnia);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 3);
        addCard(Zone.HAND, playerA, "Giant Growth");
        addCard(Zone.BATTLEFIELD, playerA, bears);

        // strict mode fails the test when an unexpected offspring question is asked
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Giant Growth", bears);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, "Giant Growth", 1);
        assertTokenCount(playerA, bears, 0);
    }
}
