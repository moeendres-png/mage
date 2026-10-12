package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class PuppetMasterStringPullerTest extends CardTestPlayerBase {

    @Test
    public void testGoadOnAttack() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Puppet Master, String Puller");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        attack(1, playerA, "Puppet Master, String Puller", playerB);
        addTarget(playerA, "Grizzly Bears");

        // goaded Bears attacks on turn 2 by itself; damage to the goader is no Treasure
        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 18);
        assertLife(playerA, 18);
        assertPermanentCount(playerA, "Treasure Token", 0);
    }
}
