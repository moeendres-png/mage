package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class ExtractPowerTest extends CardTestPlayerBase {

    @Test
    public void testPlayExiledCardsFree() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.HAND, playerA, "Extract Power");
        addCard(Zone.BATTLEFIELD, playerA, "Island", 6);
        addCard(Zone.LIBRARY, playerA, "Silvercoat Lion");
        addCard(Zone.LIBRARY, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Extract Power");
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Silvercoat Lion");
        waitStackResolved(1, PhaseStep.POSTCOMBAT_MAIN);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Grizzly Bears");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Silvercoat Lion", 1);
        assertPermanentCount(playerA, "Grizzly Bears", 1);
    }
}
