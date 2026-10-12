package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class ScarletWitchChaoticAvengerTest extends CardTestPlayerBase {

    @Test
    public void testFreeNoncreatureSpell() {
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, "Scarlet Witch, Chaotic Avenger");
        addCard(Zone.LIBRARY, playerA, "Island", 2);
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears");
        addCard(Zone.LIBRARY, playerA, "Divination");

        attack(1, playerA, "Scarlet Witch, Chaotic Avenger", playerB);
        setChoice(playerA, true);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 17);
        assertGraveyardCount(playerA, "Divination", 1);
        assertHandCount(playerA, 2);
        assertExileCount(playerA, "Grizzly Bears", 1);
    }
}
