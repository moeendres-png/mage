package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class GalactusDevourerOfWorldsTest extends CardTestPlayerBase {

    @Test
    public void testEntersExileAndForcedAttack() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Galactus, Devourer of Worlds");
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 10);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Galactus, Devourer of Worlds");
        addTarget(playerA, "Grizzly Bears");

        // no attack declared: the requirement forces Galactus to attack on turn 3
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertExileCount(playerB, "Grizzly Bears", 1);
        assertLife(playerB, 20 - 12);
    }

    @Test
    public void testNoRequirementWithSilverSurfer() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Galactus, Devourer of Worlds");
        addCard(Zone.BATTLEFIELD, playerA, "Silver Surfer, Galactus's Herald");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20);
    }
}
