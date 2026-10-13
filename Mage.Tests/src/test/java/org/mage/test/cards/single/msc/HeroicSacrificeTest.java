package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class HeroicSacrificeTest extends CardTestPlayerBase {

    @Test
    public void testRedirectAndDiesTrigger() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Heroic Sacrifice");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion");
        addCard(Zone.HAND, playerB, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerB, "Mountain");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Heroic Sacrifice", "Grizzly Bears");
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerB, "Lightning Bolt", playerA);
        addTarget(playerA, "Silvercoat Lion");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerA, 20);
        assertGraveyardCount(playerA, "Grizzly Bears", 1);
        assertHandCount(playerA, 1);
    }
}
