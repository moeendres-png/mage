package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class LokiTheDeceiverTest extends CardTestPlayerBase {

    @Test
    public void testVillainCopyAndDraw() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Loki, the Deceiver");
        addCard(Zone.BATTLEFIELD, playerA, "Iron Monger, Sadistic Tycoon");

        attack(1, playerA, "Loki, the Deceiver", playerB);
        addTarget(playerA, "Iron Monger, Sadistic Tycoon");

        checkPermanentCount("copy", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Iron Monger, Sadistic Tycoon", 2);
        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        assertLife(playerB, 20 - 4 - 2);
        assertHandCount(playerA, 1);
        assertPermanentCount(playerA, "Iron Monger, Sadistic Tycoon", 1);
    }
}
