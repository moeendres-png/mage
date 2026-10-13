package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class FirstFamilyTest extends CardTestPlayerBase {

    @Test
    public void testColorsAmongPermanentsAndSpells() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "First Family");
        addCard(Zone.BATTLEFIELD, playerA, "Tropical Island", 4);
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion");
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");

        // white and green permanents, green-blue First Family itself: X = 3
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "First Family");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertHandCount(playerA, 3);
        assertLife(playerA, 23);
    }
}
