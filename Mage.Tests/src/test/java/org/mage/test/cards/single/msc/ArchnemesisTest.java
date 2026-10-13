package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class ArchnemesisTest extends CardTestPlayerBase {

    @Test
    public void testAttackEnchantedPlayer() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Archnemesis");
        addCard(Zone.BATTLEFIELD, playerA, "Underground Sea", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Archnemesis", playerB);
        attack(1, playerA, "Grizzly Bears", playerB);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 2 - 2);
        assertLife(playerA, 20 + 2);
        assertHandCount(playerA, 1);
    }
}
