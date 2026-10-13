package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class PowerPackTest extends CardTestPlayerBase {

    @Test
    public void testFreeCastNextUpkeep() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Power Pack");
        addCard(Zone.GRAVEYARD, playerA, "Divination");

        attack(1, playerA, "Power Pack", playerB);
        // the target is chosen at random by the engine (single candidate here), no addTarget
        setChoice(playerA, true); // cast it next upkeep

        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertLife(playerB, 16);
        assertExileCount(playerA, "Divination", 1);
        assertHandCount(playerA, 1 + 2);
    }
}
