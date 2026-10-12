package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class SilverSurferGalactussHeraldTest extends CardTestPlayerBase {

    @Test
    public void testSearchForGalactus() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Silver Surfer, Galactus's Herald");
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 5);
        addCard(Zone.LIBRARY, playerA, "Galactus, Devourer of Worlds");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Silver Surfer, Galactus's Herald");
        setChoice(playerA, true);
        addTarget(playerA, "Galactus, Devourer of Worlds");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertHandCount(playerA, "Galactus, Devourer of Worlds", 1);
    }
}
