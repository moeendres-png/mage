package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class PantherHabitTest extends CardTestPlayerBase {

    @Test
    public void testDamageBecomesCounters() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Panther Habit");
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 2);
        addCard(Zone.BATTLEFIELD, playerB, "Mountain");
        addCard(Zone.HAND, playerB, "Lightning Bolt");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Equip", "Grizzly Bears");
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Lightning Bolt", "Grizzly Bears");

        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertCounterCount(playerA, "Grizzly Bears", CounterType.P1P1, 3);
        assertDamageReceived(playerA, "Grizzly Bears", 0);
    }

    @Test
    public void testUnequippedCreatureNotProtected() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Panther Habit");
        addCard(Zone.BATTLEFIELD, playerB, "Mountain");
        addCard(Zone.HAND, playerB, "Lightning Bolt");

        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Lightning Bolt", "Grizzly Bears");

        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, "Grizzly Bears", 1);
    }
}
