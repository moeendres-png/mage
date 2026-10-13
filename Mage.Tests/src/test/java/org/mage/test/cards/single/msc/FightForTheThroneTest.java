package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommanderDuelBase;

/**
 * Fight for the Throne {1}{G}
 * Instant
 * Put a +1/+1 counter on target creature you control. Then it fights target creature an opponent controls.
 * When the creature an opponent controls dies this turn, if you control your commander, you become the monarch.
 *
 * @author commander-lab
 */
public class FightForTheThroneTest extends CardTestCommanderDuelBase {

    private static final String CROWN = "Fight for the Throne";
    private static final String BEARS = "Grizzly Bears"; // our commander
    private static final String FOE = "Runeclaw Bear"; // 2/2 of the opponent

    /**
     * The commander is on the battlefield, so the dying opponent creature crowns us.
     */
    @Test
    public void testDeathOfOpponentsCreatureCrownsYouWithCommanderOnBattlefield() {
        setStrictChooseMode(true);
        addCard(Zone.COMMAND, playerA, BEARS); // commander
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 4);
        addCard(Zone.HAND, playerA, CROWN);
        addCard(Zone.BATTLEFIELD, playerB, FOE);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, BEARS); // cast the commander first
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, CROWN, BEARS);
        addTarget(playerA, FOE);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertCounterCount(playerA, BEARS, CounterType.P1P1, 1);
        assertPowerToughness(playerA, BEARS, 3, 3);
        assertGraveyardCount(playerB, FOE, 1);
        Assert.assertEquals(playerA.getId(), currentGame.getMonarchId());
    }

    /**
     * Same fight, same death, but the commander stayed in the command zone.
     */
    @Test
    public void testNoCrownWithoutYourCommanderOnTheBattlefield() {
        setStrictChooseMode(true);
        addCard(Zone.COMMAND, playerA, BEARS); // commander stays in the command zone
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant");
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);
        addCard(Zone.HAND, playerA, CROWN);
        addCard(Zone.BATTLEFIELD, playerB, FOE);

        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, CROWN, "Hill Giant");
        addTarget(playerA, FOE);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertCounterCount(playerA, "Hill Giant", CounterType.P1P1, 1);
        assertGraveyardCount(playerB, FOE, 1);
        Assert.assertNull(currentGame.getMonarchId());
    }

    /**
     * The opponent's creature dies, but our commander died in the very same fight.
     */
    @Test
    public void testNoCrownWhenYourCommanderDiesInTheSameFight() {
        setStrictChooseMode(true);
        addCard(Zone.COMMAND, playerA, BEARS); // commander, 3/3 with the counter
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 4);
        addCard(Zone.HAND, playerA, CROWN);
        addCard(Zone.BATTLEFIELD, playerB, "Hill Giant"); // 3/3 trades with it

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, BEARS);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, CROWN, BEARS);
        addTarget(playerA, "Hill Giant");
        setChoice(playerA, false); // leave the dying commander in the graveyard

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertGraveyardCount(playerA, BEARS, 1);
        assertGraveyardCount(playerB, "Hill Giant", 1);
        Assert.assertNull(currentGame.getMonarchId());
    }

    /**
     * Nothing dying means no crown at all.
     */
    @Test
    public void testNoDeathNoCrown() {
        setStrictChooseMode(true);
        addCard(Zone.COMMAND, playerA, BEARS); // commander
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 4);
        addCard(Zone.HAND, playerA, CROWN);
        addCard(Zone.BATTLEFIELD, playerB, "Pillarfield Ox"); // 2/4 survives our 3 damage

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, BEARS);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, CROWN, BEARS);
        addTarget(playerA, "Pillarfield Ox");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, BEARS, 1);
        assertPermanentCount(playerB, "Pillarfield Ox", 1);
        Assert.assertNull(currentGame.getMonarchId());
    }
}
