package org.mage.test.cards.single.mkc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Feather, Radiant Arbiter {R}{W}{W}
 * Legendary Creature -- Angel 4/3
 * Flying, lifelink
 * Whenever you cast a noncreature spell that targets only Feather, you may choose any number of other creatures
 * that spell could target and pay {2} for each of those creatures. If you do, for each of those creatures,
 * copy that spell. The copy targets that creature.
 */
public class FeatherRadiantArbiterTest extends CardTestPlayerBase {

    private static final String feather = "Feather, Radiant Arbiter";
    private static final String growth = "Giant Growth"; // {G} instant: target creature gets +3/+3 until end of turn
    private static final String bears = "Grizzly Bears"; // 2/2
    private static final String lions = "Savannah Lions"; // 2/1

    @Test
    public void testPaysTwoForEachChosenCreatureAndCopiesTheSpellForThem() {
        addCard(Zone.BATTLEFIELD, playerA, feather);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, lions);
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 4); // {2} for each of the two chosen creatures
        addCard(Zone.HAND, playerA, growth);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, growth, feather);
        setChoice(playerA, bears + "^" + lions);
        setChoice(playerA, TestPlayer.CHOICE_SKIP); // any order of the copies on the stack
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPowerToughness(playerA, feather, 7, 6);
        assertPowerToughness(playerA, bears, 5, 5);
        assertPowerToughness(playerB, lions, 5, 4);
        assertTappedCount("Mountain", true, 4);
    }

    @Test
    public void testOnlyTheChosenCreaturesGetACopy() {
        addCard(Zone.BATTLEFIELD, playerA, feather);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, lions);
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 4);
        addCard(Zone.HAND, playerA, growth);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, growth, feather);
        setChoice(playerA, bears);
        setChoice(playerA, TestPlayer.CHOICE_SKIP); // done choosing
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPowerToughness(playerA, feather, 7, 6);
        assertPowerToughness(playerA, bears, 5, 5);
        assertPowerToughness(playerB, lions, 2, 1);
        assertTappedCount("Mountain", true, 2);
    }

    @Test
    public void testNothingHappensWhenTheCopiesCannotBePaidFor() {
        addCard(Zone.BATTLEFIELD, playerA, feather);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, lions);
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 3); // {4} needed for two creatures
        addCard(Zone.HAND, playerA, growth);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, growth, feather);
        setChoice(playerA, bears + "^" + lions);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPowerToughness(playerA, feather, 7, 6);
        assertPowerToughness(playerA, bears, 2, 2);
        assertPowerToughness(playerB, lions, 2, 1);
    }

    @Test
    public void testASpellThatTargetsAnotherCreatureDoesNotTrigger() {
        addCard(Zone.BATTLEFIELD, playerA, feather);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 4);
        addCard(Zone.HAND, playerA, growth);

        // strict mode: a trigger would ask for targets that are not defined and fail the test
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, growth, bears);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPowerToughness(playerA, bears, 5, 5);
        assertPowerToughness(playerA, feather, 4, 3);
    }

    @Test
    public void testItHasFlyingAndLifelink() {
        addCard(Zone.BATTLEFIELD, playerA, feather);

        attack(1, playerA, feather);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 4);
        assertLife(playerA, 20 + 4);
    }
}
