package org.mage.test.cards.single.unf;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Space Beleren {2}{W}{U}
 * Legendary Planeswalker -- Jace
 * Space sculptor (Space Beleren divides the battlefield into alpha, beta, and gamma sectors. If a creature isn't
 * assigned to a sector, its controller assigns it to one. Opponents assign first.)
 * +1: Creatures in each sector can be blocked this turn only by creatures in the same sector.
 * -1: Put a +1/+1 counter on each creature in the sector of your choice.
 * -5: Destroy all creatures in the sector of your choice.
 */
public class SpaceBelerenTest extends CardTestPlayerBase {

    private static final String beleren = "Space Beleren";
    private static final String bears = "Grizzly Bears"; // 2/2
    private static final String giant = "Hill Giant"; // 3/3
    private static final String lions = "Savannah Lions"; // 2/1
    private static final String plus = "+1: Creatures in each sector can be blocked this turn only by creatures in the same sector";
    private static final String minus = "-1: Put a +1/+1 counter on each creature in the sector of your choice";
    private static final String ultimate = "-5: Destroy all creatures in the sector of your choice";

    private void addLands() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.HAND, playerA, beleren);
    }

    @Test
    public void testOnlyCreaturesInTheChosenSectorGetCounters() {
        addLands();
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, giant);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, beleren);
        setChoice(playerB, "Beta"); // opponents assign first
        setChoice(playerA, "Alpha"); // Grizzly Bears
        activateAbility(1, PhaseStep.POSTCOMBAT_MAIN, playerA, minus);
        setChoice(playerA, "Alpha");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertCounterCount(playerA, bears, CounterType.P1P1, 1);
        assertCounterCount(playerB, giant, CounterType.P1P1, 0);
        assertCounterCount(beleren, CounterType.LOYALTY, 2);
    }

    @Test
    public void testCreatureThatEntersLaterIsAssignedByItsController() {
        addLands();
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.HAND, playerA, lions);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, beleren);
        setChoice(playerA, "Alpha"); // Grizzly Bears
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, lions);
        setChoice(playerA, "Gamma"); // Savannah Lions
        activateAbility(3, PhaseStep.POSTCOMBAT_MAIN, playerA, minus);
        setChoice(playerA, "Gamma");
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertCounterCount(playerA, lions, CounterType.P1P1, 1);
        assertCounterCount(playerA, bears, CounterType.P1P1, 0);
    }

    @Test
    public void testDestroysEveryCreatureInTheChosenSector() {
        addLands();
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, giant);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, beleren);
        setChoice(playerB, "Alpha");
        setChoice(playerA, "Beta");
        addCounters(1, PhaseStep.BEGIN_COMBAT, playerA, beleren, CounterType.LOYALTY, 3);
        activateAbility(1, PhaseStep.POSTCOMBAT_MAIN, playerA, ultimate);
        setChoice(playerA, "Alpha");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertGraveyardCount(playerB, giant, 1);
        assertPermanentCount(playerA, bears, 1);
        assertPermanentCount(playerA, beleren, 1);
    }

    @Test
    public void testAttackerCanOnlyBeBlockedFromItsOwnSector() {
        addLands();
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, giant);
        addCard(Zone.BATTLEFIELD, playerB, "Elite Vanguard"); // 2/1

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, beleren);
        setChoice(playerB, "Beta"); // Hill Giant
        setChoice(playerB, "Alpha"); // Elite Vanguard
        setChoice(playerA, "Alpha"); // Grizzly Bears
        activateAbility(3, PhaseStep.PRECOMBAT_MAIN, playerA, plus);
        attack(3, playerA, bears);
        runCode("blockers by sector", 3, PhaseStep.DECLARE_ATTACKERS, playerA, (info, player, game) -> {
            Permanent attacker = getPermanent(bears, playerA);
            Assert.assertFalse("Beta can't block Alpha", getPermanent(giant, playerB).canBlock(attacker.getId(), game));
            Assert.assertTrue("Alpha can block Alpha", getPermanent("Elite Vanguard", playerB).canBlock(attacker.getId(), game));
        });
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.END_COMBAT);
        execute();
    }

    @Test
    public void testWithoutThePlusAbilityEveryCreatureMayBlock() {
        addLands();
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, giant);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, beleren);
        setChoice(playerB, "Beta");
        setChoice(playerA, "Alpha");
        attack(1, playerA, bears);
        runCode("blockers by sector", 1, PhaseStep.DECLARE_ATTACKERS, playerA, (info, player, game) ->
                Assert.assertTrue(getPermanent(giant, playerB).canBlock(getPermanent(bears, playerA).getId(), game)));
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();
    }
}
