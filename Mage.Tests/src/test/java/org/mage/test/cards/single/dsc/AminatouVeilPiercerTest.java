package org.mage.test.cards.single.dsc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Aminatou, Veil Piercer {1}{W}{U}{B} 2/4
 * At the beginning of your upkeep, surveil 2.
 * Each enchantment card in your hand has miracle. Its miracle cost is equal to its mana cost reduced by {4}.
 */
public class AminatouVeilPiercerTest extends CardTestPlayerBase {

    private static final String aminatou = "Aminatou, Veil Piercer";
    private static final String anthem = "Glorious Anthem"; // {1}{W}{W} enchantment, miracle cost {W}{W}

    @Test
    public void testFirstDrawOfTheTurnCanBeCastForItsReducedCost() {
        setupAminatou();
        addCard(Zone.HAND, playerA, aminatou);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Island", 3);
        addCard(Zone.LIBRARY, playerA, "Island"); // second card of the library
        addCard(Zone.LIBRARY, playerA, anthem); // last added card is the top card

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, aminatou);
        // turn 3 upkeep surveil 2 sees the Anthem and an Island: nothing to the graveyard, Anthem stays on top
        addTarget(playerA, TestPlayer.TARGET_SKIP);
        setChoice(playerA, "Island");
        // turn 3 draw: Glorious Anthem is the first card drawn
        setChoice(playerA, true); // reveal it and cast it for its miracle cost
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertPermanentCount(playerA, anthem, 1);
        assertTappedCount("Plains", true, 2);
    }

    @Test
    public void testNonEnchantmentGetsNoMiracle() {
        setupAminatou();
        addCard(Zone.HAND, playerA, aminatou);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Island", 4);
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, aminatou);
        addTarget(playerA, TestPlayer.TARGET_SKIP);
        setChoice(playerA, "Island");
        // no miracle question may be asked for a creature card
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertHandCount(playerA, "Grizzly Bears", 1);
    }

    @Test
    public void testWithoutAminatouTheEnchantmentHasNoMiracle() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Island", 3);
        addCard(Zone.LIBRARY, playerA, anthem);

        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertHandCount(playerA, anthem, 1);
        assertPermanentCount(playerA, anthem, 0);
    }

    @Test
    public void testOnlyTheFirstCardDrawnThisTurnHasMiracle() {
        setupAminatou();
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.HAND, playerA, aminatou);
        addCard(Zone.HAND, playerA, "Think Twice"); // {1}{U} instant, draw a card
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Island", 3);
        addCard(Zone.LIBRARY, playerA, anthem);
        addCard(Zone.LIBRARY, playerA, "Island"); // top: drawn by Think Twice

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, aminatou);
        // an Island is drawn in the turn 3 upkeep, the Anthem is the second card drawn this turn: no miracle
        castSpell(3, PhaseStep.UPKEEP, playerA, "Think Twice");
        addTarget(playerA, TestPlayer.TARGET_SKIP);
        setChoice(playerA, "Island");
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertHandCount(playerA, anthem, 1);
        assertPermanentCount(playerA, anthem, 0);
    }

    private void setupAminatou() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp");
    }
}
