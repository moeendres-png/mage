package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * The Cyber-Controller {X}{U}{U}{B} 3/3 legendary artifact creature
 * When The Cyber-Controller enters, each opponent mills X cards. Put all creature cards milled this way onto the
 * battlefield face down under your control. They're 2/2 Cyberman artifact creatures.
 * Other artifact creatures you control get +1/+1.
 */
public class TheCyberControllerTest extends CardTestPlayerBase {

    private static final String controller = "The Cyber-Controller";

    private void setUpLibrary() {
        removeAllCardsFromLibrary(playerB);
        skipInitShuffling();
        addCard(Zone.LIBRARY, playerB, "Mountain", 5);
        // milled with X=3, top card last: Grizzly Bears, Island, Savannah Lions
        addCard(Zone.LIBRARY, playerB, "Savannah Lions");
        addCard(Zone.LIBRARY, playerB, "Island");
        addCard(Zone.LIBRARY, playerB, "Grizzly Bears");
    }

    @Test
    public void testMilledCreaturesBecomeCybermenAndOthersStayInTheGraveyard() {
        setUpLibrary();
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 4);
        addCard(Zone.HAND, playerA, controller);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, controller);
        setChoice(playerA, "X=3");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, controller, 1);
        CybermanAssert.assertCybermen(currentGame, playerA, 2);
        assertGraveyardCount(playerB, "Island", 1);
        assertGraveyardCount(playerB, "Grizzly Bears", 0);
        assertGraveyardCount(playerB, "Savannah Lions", 0);
        assertLibraryCount(playerB, 5);
    }

    @Test
    public void testOtherArtifactCreaturesGetPlusOnePlusOne() {
        setUpLibrary();
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 4);
        addCard(Zone.BATTLEFIELD, playerA, "Ornithopter"); // 0/2 artifact creature
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears"); // not an artifact
        addCard(Zone.HAND, playerA, controller);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, controller);
        setChoice(playerA, "X=3");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPowerToughness(playerA, "Ornithopter", 1, 3);
        assertPowerToughness(playerA, "Grizzly Bears", 2, 2);
        assertPowerToughness(playerA, controller, 3, 3); // only the others
        org.junit.Assert.assertEquals(3, CybermanAssert.faceDown(currentGame, playerA).get(0).getPower().getValue());
    }

    @Test
    public void testNoCreatureMilledNoCyberman() {
        removeAllCardsFromLibrary(playerB);
        skipInitShuffling();
        addCard(Zone.LIBRARY, playerB, "Island", 6);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 3);
        addCard(Zone.HAND, playerA, controller);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, controller);
        setChoice(playerA, "X=2");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        CybermanAssert.assertCybermen(currentGame, playerA, 0);
        assertGraveyardCount(playerB, "Island", 2);
    }
}
