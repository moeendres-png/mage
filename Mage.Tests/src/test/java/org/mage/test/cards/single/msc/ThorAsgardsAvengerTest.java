package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class ThorAsgardsAvengerTest extends CardTestPlayerBase {

    @Test
    public void testOtherSourcesOnly() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Thor, Asgard's Avenger");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", playerB);
        attack(1, playerA, "Thor, Asgard's Avenger", playerB);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 4 - 4);
    }
}
