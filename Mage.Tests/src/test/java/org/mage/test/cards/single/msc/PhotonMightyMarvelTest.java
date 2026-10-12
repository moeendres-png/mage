package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class PhotonMightyMarvelTest extends CardTestPlayerBase {

    @Test
    public void testCombatDamageMana() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Photon, Mighty Marvel");
        addCard(Zone.HAND, playerA, "Grizzly Bears");

        attack(1, playerA, "Photon, Mighty Marvel", playerB);
        setChoice(playerA, "Green");
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Grizzly Bears");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 18);
        assertPermanentCount(playerA, "Grizzly Bears", 1);
    }
}
