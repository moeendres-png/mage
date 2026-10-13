package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class WillieLumpkinPostmanTest extends CardTestPlayerBase {

    @Test
    public void testDrawAndAttackRestriction() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Willie Lumpkin, Postman");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        attack(1, playerA, "Willie Lumpkin, Postman", playerB);
        setChoice(playerB, true); // opponent draws

        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 19);
        assertHandCount(playerA, 1);
        assertHandCount(playerB, 2); // own draw step plus Willie's draw
        assertPermanentCount(playerB, "Grizzly Bears", 1);
    }
}
