package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Rassilon, the War President {3}{U}{B} 3/4
 * At the beginning of your upkeep, you lose 2 life and exile the top card of your library.
 * You may play that card for as long as it remains exiled.
 * Each noncreature spell you cast from exile has conspire.
 */
public class RassilonTheWarPresidentTest extends CardTestPlayerBase {

    private static final String rassilon = "Rassilon, the War President";
    private static final String murder = "Murder"; // {1}{B}{B} instant: destroy target creature

    @Test
    public void testUpkeepExilesTopCardLosesLifeAndTheCardIsPlayable() {
        addCard(Zone.BATTLEFIELD, playerA, rassilon);
        // a single card: the library is shuffled at the start of the game, so more cards would be in random order
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Island");

        playLand(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Island"); // exiled by the upkeep of turn 1, can only come from exile
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertLife(playerA, 20 - 2);
        assertPermanentCount(playerA, "Island", 1);
        assertExileCount(playerA, "Island", 0);
        assertLibraryCount(playerA, 0);
    }

    @Test
    public void testNoncreatureSpellCastFromExileCanBeConspired() {
        addCard(Zone.BATTLEFIELD, playerA, rassilon);
        addCard(Zone.BATTLEFIELD, playerA, "Walking Corpse"); // black: shares a color with Murder
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, murder); // exiled by the upkeep of turn 1
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerB, "Savannah Lions");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, murder, "Grizzly Bears");
        setChoice(playerA, true); // pay the conspire cost
        setChoice(playerA, "Rassilon, the War President^Walking Corpse"); // tap these two
        setChoice(playerA, true); // choose new targets for the copy
        addTarget(playerA, "Savannah Lions");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertGraveyardCount(playerB, "Savannah Lions", 1); // destroyed by the copy
        assertTapped(rassilon, true);
        assertTapped("Walking Corpse", true);
    }

    @Test
    public void testACreatureSpellCastFromExileHasNoConspire() {
        addCard(Zone.BATTLEFIELD, playerA, rassilon);
        addCard(Zone.BATTLEFIELD, playerA, "Walking Corpse");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 4);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Gutter Skulk"); // {2}{B} creature, exiled by the upkeep of turn 1

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Gutter Skulk");
        // strict mode: a conspire prompt would be an undefined choice and fail the test
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Gutter Skulk", 1);
        assertTapped(rassilon, false);
    }

    @Test
    public void testASpellFromHandHasNoConspire() {
        addCard(Zone.BATTLEFIELD, playerA, rassilon);
        addCard(Zone.BATTLEFIELD, playerA, "Walking Corpse");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 3);
        addCard(Zone.HAND, playerA, murder);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Forest");

        // strict mode: a conspire prompt would be an undefined choice and fail the test
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, murder, "Grizzly Bears");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertTapped(rassilon, false);
    }
}
