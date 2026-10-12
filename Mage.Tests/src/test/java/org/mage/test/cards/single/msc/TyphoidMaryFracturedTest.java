package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class TyphoidMaryFracturedTest extends CardTestPlayerBase {

    @Test
    public void testChooseAfterDiscard() {
        addCard(Zone.BATTLEFIELD, playerA, "Typhoid Mary, Fractured");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Faithless Looting");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Faithless Looting");
        attack(1, playerA, "Typhoid Mary, Fractured", playerB);
        setChoice(playerA, "Bloody Mary");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 2 - 3);
        assertLife(playerA, 22);
    }

    @Test
    public void testRandomModeWithoutDiscard() {
        addCard(Zone.BATTLEFIELD, playerA, "Typhoid Mary, Fractured");

        attack(1, playerA, "Typhoid Mary, Fractured", playerB);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        int outcomes = (currentGame.getBattlefield().count(new mage.filter.common.FilterControlledPermanent(), playerA.getId(), null, currentGame) == 2 ? 1 : 0)
                + (playerA.getHand().size() == 1 ? 1 : 0)
                + (playerA.getLife() == 22 ? 1 : 0);
        Assert.assertEquals("exactly one mode", 1, outcomes);
    }
}
