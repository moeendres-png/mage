package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class WakandaForeverTest extends CardTestPlayerBase {

    @Test
    public void testOneToBattlefieldOneToHandRestToGraveyard() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.HAND, playerA, "Wakanda Forever!");
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 6);
        addCard(Zone.LIBRARY, playerA, "Lightning Bolt", 2);
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears");
        addCard(Zone.LIBRARY, playerA, "Hill Giant");
        addCard(Zone.LIBRARY, playerA, "Island");
        addCard(Zone.LIBRARY, playerA, "Ornithopter");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Wakanda Forever!");
        setChoice(playerA, "Hill Giant"); // onto the battlefield
        setChoice(playerA, "Grizzly Bears"); // into hand

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Hill Giant", 1);
        assertCounterCount(playerA, "Hill Giant", CounterType.INDESTRUCTIBLE, 1);
        assertHandCount(playerA, "Grizzly Bears", 1);
        assertGraveyardCount(playerA, "Lightning Bolt", 2);
        assertGraveyardCount(playerA, "Island", 1);
        assertGraveyardCount(playerA, "Ornithopter", 1);
    }
}
