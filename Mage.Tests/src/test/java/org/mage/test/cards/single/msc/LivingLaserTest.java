package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class LivingLaserTest extends CardTestPlayerBase {

    @Test
    public void testTokensPerDiscard() {
        addCard(Zone.BATTLEFIELD, playerA, "Living Laser");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Faithless Looting");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Faithless Looting");
        attack(1, playerA, "Living Laser", playerB);

        checkPermanentCount("tokens", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Living Laser", 3);
        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        assertLife(playerB, 20 - 4 * 3);
        assertPermanentCount(playerA, "Living Laser", 1);
    }
}
