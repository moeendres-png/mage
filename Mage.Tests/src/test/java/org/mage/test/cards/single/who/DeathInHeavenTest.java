package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Death in Heaven {3}{B} Saga
 * I, II -- Target player mills two cards, then exiles their graveyard.
 * III -- Put all creature cards exiled with this enchantment onto the battlefield face down under your control.
 * They're 2/2 Cyberman artifact creatures.
 */
public class DeathInHeavenTest extends CardTestPlayerBase {

    private static final String saga = "Death in Heaven";

    @Test
    public void testCreatureCardsExiledByTheChaptersComeBackAsCybermen() {
        removeAllCardsFromLibrary(playerB);
        skipInitShuffling();
        // the last card added is the top card: milled by chapter I are Savannah Lions and Island
        addCard(Zone.LIBRARY, playerB, "Mountain", 6);
        addCard(Zone.LIBRARY, playerB, "Island");
        addCard(Zone.LIBRARY, playerB, "Savannah Lions");
        addCard(Zone.GRAVEYARD, playerB, "Grizzly Bears");
        addCard(Zone.GRAVEYARD, playerB, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 4);
        addCard(Zone.HAND, playerA, saga);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, saga);
        addTarget(playerA, playerB); // chapter I
        addTarget(playerA, playerB); // chapter II
        setStrictChooseMode(true);
        setStopAt(5, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerB, 0); // everything was exiled
        // Grizzly Bears, Savannah Lions (milled with chapter I) and Island, Lightning Bolt stay exiled
        CybermanAssert.assertCybermen(currentGame, playerA, 2);
        assertExileCount(playerB, "Lightning Bolt", 1);
        assertExileCount(playerB, "Island", 1);
        assertGraveyardCount(playerA, saga, 1); // sacrificed after III
    }

    @Test
    public void testNothingComesBackBeforeChapterThree() {
        addCard(Zone.GRAVEYARD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 4);
        addCard(Zone.HAND, playerA, saga);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, saga);
        addTarget(playerA, playerB); // chapter I
        addTarget(playerA, playerB); // chapter II
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.BEGIN_COMBAT);
        execute();

        assertExileCount(playerB, "Grizzly Bears", 1);
        CybermanAssert.assertCybermen(currentGame, playerA, 0);
    }
}
