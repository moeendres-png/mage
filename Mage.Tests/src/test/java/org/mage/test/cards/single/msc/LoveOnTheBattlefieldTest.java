package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class LoveOnTheBattlefieldTest extends CardTestPlayerBase {

    @Test
    public void testExactlyTwoAttackers() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Love on the Battlefield");
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion");

        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Silvercoat Lion", playerB);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertHandCount(playerA, 1);
        assertLife(playerB, 16);
        assertCounterCount(playerA, "Grizzly Bears", CounterType.P1P1, 1);
        assertCounterCount(playerA, "Silvercoat Lion", CounterType.P1P1, 1);
    }
}
