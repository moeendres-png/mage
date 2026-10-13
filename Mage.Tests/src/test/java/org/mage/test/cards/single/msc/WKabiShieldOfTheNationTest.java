package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommanderDuelBase;

/**
 * "Whenever you attack with your commander, if you control an artifact with mana value 4 or
 * greater, create a 4/4 green Rhino creature token with trample."
 *
 * @author commander-lab
 */
public class WKabiShieldOfTheNationTest extends CardTestCommanderDuelBase {

    private void setUpCommander() {
        addCard(Zone.COMMAND, playerA, "Grizzly Bears"); // the commander
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);
        addCard(Zone.BATTLEFIELD, playerA, "W'Kabi, Shield of the Nation");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Grizzly Bears");
    }

    @Test
    public void testRhinoWhenCommanderAttacksWithBigArtifact() {
        setStrictChooseMode(true);
        setUpCommander();
        addCard(Zone.BATTLEFIELD, playerA, "Panther Habit"); // artifact, mana value 4
        attack(3, playerA, "Grizzly Bears", playerB);

        setStopAt(3, PhaseStep.END_COMBAT);
        execute();

        assertPermanentCount(playerA, "Rhino Token", 1);
    }

    @Test
    public void testNoRhinoWithoutBigArtifact() {
        setStrictChooseMode(true);
        setUpCommander();
        addCard(Zone.BATTLEFIELD, playerA, "Sol Ring"); // mana value 1
        attack(3, playerA, "Grizzly Bears", playerB);

        setStopAt(3, PhaseStep.END_COMBAT);
        execute();

        assertPermanentCount(playerA, "Rhino Token", 0);
    }

    @Test
    public void testNoRhinoWhenOnlyANoncommanderAttacks() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "W'Kabi, Shield of the Nation");
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant");
        addCard(Zone.BATTLEFIELD, playerA, "Panther Habit");
        attack(1, playerA, "Hill Giant", playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertPermanentCount(playerA, "Rhino Token", 0);
    }
}
