package org.mage.test.cards.single.frc;

import mage.abilities.keyword.ProtectionFromEverythingAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Teferi's Reproach {2}{W} instant
 * Choose target opponent. Until that player's next turn, they gain protection from everything and their life total
 * can't change. All nonland permanents they control phase out. Exile Teferi's Reproach.
 */
public class TeferisReproachTest extends CardTestPlayerBase {

    private static final String reproach = "Teferi's Reproach";

    @Test
    public void testPhaseOutLifeLockAndExile() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 4);
        addCard(Zone.HAND, playerA, reproach);
        addCard(Zone.HAND, playerA, "Rolling Earthquake"); // X damage to each creature and each player
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, reproach, playerB);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Rolling Earthquake");
        setChoice(playerA, "X=2");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertExileCount(playerA, reproach, 1);
        assertGraveyardCount(playerA, reproach, 0);
        assertLife(playerB, 20); // life total can't change
        assertLife(playerA, 18);
        assertPermanentCount(playerB, "Grizzly Bears", 0); // phased out
        assertGraveyardCount(playerB, "Grizzly Bears", 0); // and so not hit by the earthquake
    }

    @Test
    public void testPermanentsPhaseInOnTheTargetsNextTurn() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.HAND, playerA, reproach);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerB, "Forest");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, reproach, playerB);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertPermanentCount(playerB, "Grizzly Bears", 1); // phased in again
        assertPermanentCount(playerB, "Forest", 1); // lands never phased out
    }

    @Test
    public void testProtectionFromEverythingUntilTheirTurn() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.HAND, playerA, reproach);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, reproach, playerB);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        org.junit.Assert.assertTrue("target has protection from everything",
                currentGame.getPlayer(playerB.getId()).getAbilities().containsClass(ProtectionFromEverythingAbility.class));
    }
}
