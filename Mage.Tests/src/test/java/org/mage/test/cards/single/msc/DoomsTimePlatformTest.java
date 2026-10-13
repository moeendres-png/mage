package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class DoomsTimePlatformTest extends CardTestPlayerBase {

    @Test
    public void testSuspendFromGraveyard() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Doom's Time Platform");
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.GRAVEYARD, playerA, "Divination");

        attack(1, playerA, "Grizzly Bears", playerB);
        addTarget(playerA, "Divination");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertExileCount(playerA, "Divination", 1);
        assertCounterOnExiledCardCount("Divination", CounterType.TIME, 2);
    }
}
