package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * The War Doctor {2}{R}{W} 3/5
 * Whenever one or more other permanents phase out and whenever one or more other cards are put into exile
 * from anywhere, put a time counter on The War Doctor.
 * Whenever The War Doctor attacks, it deals damage equal to the number of time counters on it to any target.
 * If a creature dealt damage this way would die this turn, exile it instead.
 */
public class TheWarDoctorTest extends CardTestPlayerBase {

    private static final String doctor = "The War Doctor";

    @Test
    public void testAnotherPermanentPhasingOutAddsOneCounter() {
        addCard(Zone.BATTLEFIELD, playerA, doctor);
        addCard(Zone.BATTLEFIELD, playerA, "Rainbow Efreet");
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{U}{U}: {this} phases out");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertCounterCount(doctor, CounterType.TIME, 1);
    }

    @Test
    public void testExilingACardAddsACounterButAllAtOnceOnlyOne() {
        addCard(Zone.BATTLEFIELD, playerA, doctor);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.HAND, playerA, "Settle the Wreckage");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerB, "Savannah Lions");

        attack(2, playerB, "Grizzly Bears");
        attack(2, playerB, "Savannah Lions");
        castSpell(2, PhaseStep.DECLARE_ATTACKERS, playerA, "Settle the Wreckage", playerB);
        setChoice(playerB, false); // do not search for basic lands
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertExileCount(playerB, "Grizzly Bears", 1);
        assertExileCount(playerB, "Savannah Lions", 1);
        assertCounterCount(doctor, CounterType.TIME, 1); // two cards exiled at the same time: one trigger
    }

    @Test
    public void testASingleExileAddsACounter() {
        addCard(Zone.BATTLEFIELD, playerA, doctor);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 1);
        addCard(Zone.HAND, playerA, "Path to Exile");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Path to Exile", "Grizzly Bears");
        setChoice(playerB, false); // do not search for a basic land
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertExileCount(playerB, "Grizzly Bears", 1);
        assertCounterCount(doctor, CounterType.TIME, 1);
    }

    @Test
    public void testAttackDealsDamageEqualToCountersAndExilesWhatWouldDie() {
        addCard(Zone.BATTLEFIELD, playerA, doctor);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCounters(1, PhaseStep.PRECOMBAT_MAIN, playerA, doctor, CounterType.TIME, 2);

        attack(1, playerA, doctor);
        addTarget(playerA, "Grizzly Bears");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertExileCount(playerB, "Grizzly Bears", 1); // 2 damage kills a 2/2: exiled, not in the graveyard
        assertGraveyardCount(playerB, "Grizzly Bears", 0);
    }

    @Test
    public void testAttackWithNoCountersDealsNoDamage() {
        addCard(Zone.BATTLEFIELD, playerA, doctor);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        attack(1, playerA, doctor);
        addTarget(playerA, "Grizzly Bears");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerB, "Grizzly Bears", 1);
        assertDamageReceived(playerB, "Grizzly Bears", 0);
    }

    @Test
    public void testAttackCanTargetAPlayer() {
        addCard(Zone.BATTLEFIELD, playerA, doctor);
        addCounters(1, PhaseStep.PRECOMBAT_MAIN, playerA, doctor, CounterType.TIME, 3);

        attack(1, playerA, doctor);
        addTarget(playerA, playerB);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 3 - 3); // the 3 damage of the trigger and the 3 combat damage
    }
}
