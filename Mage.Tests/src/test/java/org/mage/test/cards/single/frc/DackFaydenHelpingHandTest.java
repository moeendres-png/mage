package org.mage.test.cards.single.frc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Dack Fayden, Helping Hand {4}{W}{W} 4/6
 * When Dack Fayden enters, reveal cards from the top of your library until you reveal X creature cards, where X is
 * the number of opponents you have. Put those creature cards onto the battlefield, then shuffle. They're goaded for
 * the rest of the game. For each of those permanents, choose a different opponent. Each opponent gains control of the
 * permanent for which they were chosen.
 */
public class DackFaydenHelpingHandTest extends CardTestPlayerBase {

    private static final String dack = "Dack Fayden, Helping Hand";

    @Test
    public void testOpponentGainsControlOfGoadedCreature() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 6);
        addCard(Zone.HAND, playerA, dack);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Forest", 3);
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears"); // top

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, dack);
        setChoice(playerA, "PlayerB"); // opponent who gains control
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, dack, 1);
        assertPermanentCount(playerA, "Grizzly Bears", 0);
        assertPermanentCount(playerB, "Grizzly Bears", 1);
        org.junit.Assert.assertFalse("the creature is goaded",
                getPermanent("Grizzly Bears", playerB).getGoadingPlayers().isEmpty());
    }

    @Test
    public void testControlStaysAfterTheTurnEnds() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 6);
        addCard(Zone.HAND, playerA, dack);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Forest", 3);
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, dack);
        setChoice(playerA, "PlayerB"); // opponent who gains control
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.UPKEEP);
        execute();

        assertPermanentCount(playerB, "Grizzly Bears", 1);
    }
}
