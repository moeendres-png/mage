package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class HelmutZemoMastermindTest extends CardTestPlayerBase {

    @Test
    public void testCastFromGraveyardOnAttack() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Helmut Zemo, Mastermind");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.GRAVEYARD, playerA, "Lightning Bolt");

        attack(1, playerA, "Helmut Zemo, Mastermind", playerB);
        addTarget(playerA, "Lightning Bolt");
        setChoice(playerA, true); // cast it
        addTarget(playerA, playerB); // bolt target

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertExileCount(playerA, "Lightning Bolt", 1);
        assertCounterCount(playerA, "Helmut Zemo, Mastermind", CounterType.P1P1, 1);
        assertLife(playerB, 20 - 3 - 3);
    }
}
