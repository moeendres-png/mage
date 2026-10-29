package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Cybership {6} artifact -- Vehicle 8/8
 * Flying
 * Whenever this Vehicle deals combat damage to a player, put the top two cards of that player's library onto the
 * battlefield face down under your control. They're 2/2 Cyberman artifact creatures.
 * Crew 4
 */
public class CybershipTest extends CardTestPlayerBase {

    private static final String ship = "Cybership";

    @Test
    public void testCombatDamagePutsTheTopTwoCardsOntoTheBattlefieldAsCybermen() {
        removeAllCardsFromLibrary(playerB);
        skipInitShuffling();
        addCard(Zone.LIBRARY, playerB, "Mountain", 5);
        addCard(Zone.LIBRARY, playerB, "Island"); // second from the top
        addCard(Zone.LIBRARY, playerB, "Grizzly Bears"); // top
        addCard(Zone.BATTLEFIELD, playerA, ship);
        addCard(Zone.BATTLEFIELD, playerA, "Craw Wurm"); // power 6 crews it

        activateAbility(1, PhaseStep.BEGIN_COMBAT, playerA, "Crew 4");
        setChoice(playerA, "Craw Wurm");
        attack(1, playerA, ship);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20 - 8);
        CybermanAssert.assertCybermen(currentGame, playerA, 2); // Grizzly Bears and Island, even the land
        assertLibraryCount(playerB, 5);
    }

    @Test
    public void testNoTriggerWithoutCombatDamage() {
        removeAllCardsFromLibrary(playerB);
        skipInitShuffling();
        addCard(Zone.LIBRARY, playerB, "Mountain", 5);
        addCard(Zone.BATTLEFIELD, playerA, ship);
        addCard(Zone.BATTLEFIELD, playerA, "Craw Wurm");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        CybermanAssert.assertCybermen(currentGame, playerA, 0);
        assertLibraryCount(playerB, 5);
    }
}
