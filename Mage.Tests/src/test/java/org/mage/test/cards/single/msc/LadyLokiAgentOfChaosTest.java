package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class LadyLokiAgentOfChaosTest extends CardTestPlayerBase {

    @Test
    public void testExileSpellDamageAndFreeCast() {
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, "Lady Loki, Agent of Chaos");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.LIBRARY, playerA, "Divination");
        addCard(Zone.LIBRARY, playerA, "Island");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", playerB);
        setChoice(playerA, true); // cast Divination free

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // Bolt exiled before it resolves; |1 - 3| = 2 damage
        assertExileCount(playerA, "Lightning Bolt", 1);
        assertLife(playerB, 18);
        assertGraveyardCount(playerA, "Divination", 1);
        assertHandCount(playerA, 2);
    }
}
