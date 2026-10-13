package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * "Whenever a creature you control connives, put a +1/+1 counter on each Villain you control."
 *
 * @author commander-lab
 */
public class IronMongerSadisticTycoonTest extends CardTestPlayerBase {

    private static final String MONGER = "Iron Monger, Sadistic Tycoon";

    @Test
    public void testConnivePutsCounterOnEachVillain() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, MONGER); // Villain
        addCard(Zone.BATTLEFIELD, playerA, "Batroc the Leaper"); // Villain
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears"); // not a Villain
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.HAND, playerA, "Raffine's Informant"); // ETB: it connives
        addCard(Zone.HAND, playerA, "Plains");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Raffine's Informant");
        setChoice(playerA, "Plains"); // connive discard: a land, so no connive counter

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertCounterCount(playerA, MONGER, CounterType.P1P1, 1);
        assertCounterCount(playerA, "Batroc the Leaper", CounterType.P1P1, 1);
        assertCounterCount(playerA, "Grizzly Bears", CounterType.P1P1, 0);
        assertCounterCount(playerA, "Raffine's Informant", CounterType.P1P1, 0);
    }

    @Test
    public void testOpponentsConniveDoesNotTrigger() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, MONGER);
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 2);
        addCard(Zone.HAND, playerB, "Raffine's Informant");
        addCard(Zone.HAND, playerB, "Plains");

        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Raffine's Informant");
        setChoice(playerB, "Plains");

        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertCounterCount(playerA, MONGER, CounterType.P1P1, 0);
    }
}
