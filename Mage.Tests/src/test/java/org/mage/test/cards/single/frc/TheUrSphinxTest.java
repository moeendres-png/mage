package org.mage.test.cards.single.frc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * The Ur-Sphinx {6}{W}{U}{B} 10/10
 * Eminence -- As long as The Ur-Sphinx is in the command zone or on the battlefield, other Sphinx spells you cast cost {1} less.
 * Flying
 * Whenever one or more Sphinxes you control attack, each player mills that many cards. For each player, you may cast
 * a card that player milled this way without paying its mana cost.
 */
public class TheUrSphinxTest extends CardTestPlayerBase {

    private static final String sphinx = "The Ur-Sphinx";

    @Test
    public void testReducesOtherSphinxSpellsOnBattlefield() {
        addCard(Zone.BATTLEFIELD, playerA, sphinx);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 6);
        addCard(Zone.HAND, playerA, "Sphinx Ambassador"); // {5}{U}{U}

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Sphinx Ambassador");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Sphinx Ambassador", 1);
    }

    @Test
    public void testNoReductionWithoutIt() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 6);
        addCard(Zone.HAND, playerA, "Sphinx Ambassador");

        checkPlayableAbility("no discount without The Ur-Sphinx", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                "Cast Sphinx Ambassador", false);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void testAttackMillsAndCastsFree() {
        addCard(Zone.BATTLEFIELD, playerA, sphinx);
        removeAllCardsFromLibrary(playerA);
        removeAllCardsFromLibrary(playerB);
        addCard(Zone.LIBRARY, playerA, "Forest", 2);
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears"); // milled, can be cast for free
        addCard(Zone.LIBRARY, playerB, "Forest", 2);
        addCard(Zone.LIBRARY, playerB, "Silvercoat Lion"); // milled, can be cast for free

        attack(1, playerA, sphinx);
        setChoice(playerA, true); // cast the card milled from A's library
        setChoice(playerA, true); // cast the card milled from B's library
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertPermanentCount(playerA, "Silvercoat Lion", 1);
        assertLife(playerB, 10);
    }
}
