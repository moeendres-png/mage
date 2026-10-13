package org.mage.test.cards.single.clb;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class DurnanOfTheYawningPortalTest extends CardTestPlayerBase {

    private static final String DURNAN = "Durnan of the Yawning Portal";

    private void attackAndExileHillGiant() {
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, DURNAN);
        addCard(Zone.LIBRARY, playerA, "Island", 3);
        addCard(Zone.LIBRARY, playerA, "Hill Giant"); // {3}{R}, top card
        attack(1, playerA, DURNAN, playerB);
        setChoice(playerA, "Hill Giant"); // exile it
        setChoice(playerA, "Island", 2); // order the three Islands put on the bottom
    }

    @Test
    public void testCastFromExileWithUndaunted() {
        setStrictChooseMode(true);
        attackAndExileHillGiant();
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 3); // 4 - 1 opponent = 3

        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Hill Giant");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Hill Giant", 1);
        assertLibraryCount(playerA, "Island", 3); // the rest went to the bottom
    }

    @Test
    public void testNotCastableWithoutTheReduction() {
        setStrictChooseMode(true);
        attackAndExileHillGiant();
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 2);

        checkPlayableAbility("needs 3 mana", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Cast Hill Giant", false);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertExileCount(playerA, "Hill Giant", 1);
    }

    @Test
    public void testDeclineExile() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, DURNAN);
        addCard(Zone.LIBRARY, playerA, "Island", 3);
        addCard(Zone.LIBRARY, playerA, "Hill Giant");
        attack(1, playerA, DURNAN, playerB);
        setChoice(playerA, TestPlayer.CHOICE_SKIP); // exile nothing
        setChoice(playerA, "Hill Giant"); // order all four on the bottom
        setChoice(playerA, "Island", 2);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertExileCount(playerA, "Hill Giant", 0);
        assertLibraryCount(playerA, "Hill Giant", 1);
    }
}
