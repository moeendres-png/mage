package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class LockjawSlobberingTeleporterTest extends CardTestPlayerBase {

    @Test
    public void testCounterAfterNoncreatureSpell() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Lockjaw, Slobbering Teleporter");
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerB, "Hill Giant");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", playerB);
        addTarget(playerA, "Grizzly Bears");

        setStopAt(1, PhaseStep.DECLARE_ATTACKERS);
        execute();

        assertCounterCount(playerA, "Lockjaw, Slobbering Teleporter", CounterType.P1P1, 1);
    }

    @Test
    public void testNoCounterWithoutSpell() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Lockjaw, Slobbering Teleporter");

        setStopAt(1, PhaseStep.DECLARE_ATTACKERS);
        execute();

        assertCounterCount(playerA, "Lockjaw, Slobbering Teleporter", CounterType.P1P1, 0);
    }
}
