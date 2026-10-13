package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class ShuriTheBlackPantherTest extends CardTestPlayerBase {

    private static final String SHURI = "Shuri, the Black Panther";

    @Test
    public void testSixArtifactsDrawAndPump() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, SHURI);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Ornithopter", 6);
        attack(1, playerA, SHURI, playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertHandCount(playerA, 1);
        assertPowerToughness(playerA, "Grizzly Bears", 4, 4);
        assertLife(playerB, 20 - 4);
        assertLife(playerA, 20 + 4); // lifelink
    }

    @Test
    public void testThreeArtifactsDrawOnly() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, SHURI);
        addCard(Zone.BATTLEFIELD, playerA, "Ornithopter", 3);
        attack(1, playerA, SHURI, playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertHandCount(playerA, 1);
        assertLife(playerB, 20 - 2);
    }

    @Test
    public void testTwoArtifactsNothing() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, SHURI);
        addCard(Zone.BATTLEFIELD, playerA, "Ornithopter", 2);
        attack(1, playerA, SHURI, playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertHandCount(playerA, 0);
    }
}
