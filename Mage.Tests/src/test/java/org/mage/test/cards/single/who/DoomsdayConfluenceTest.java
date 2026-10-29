package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Doomsday Confluence {X}{X}{B} sorcery
 * Choose X. You may choose the same mode more than once.
 * * Each player sacrifices a nonartifact creature of their choice.
 * * Create a 3/3 black Dalek artifact creature token with menace.
 * * Each opponent discards a card.
 */
public class DoomsdayConfluenceTest extends CardTestPlayerBase {

    private static final String confluence = "Doomsday Confluence";
    private static final String sacrifice = "Each player sacrifices a nonartifact creature of their choice";
    private static final String dalek = "Create a 3/3 black Dalek artifact creature token with menace";
    private static final String discard = "Each opponent discards a card";

    @Test
    public void testSameModeTwiceMakesTwoDaleks() {
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 5);
        addCard(Zone.HAND, playerA, confluence);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, confluence);
        setChoice(playerA, "X=2");
        setChoice(playerA, dalek);
        setChoice(playerA, dalek);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Dalek Token", 2);
        assertGraveyardCount(playerA, confluence, 1);
    }

    @Test
    public void testSacrificeAndDiscardInPrintedOrder() {
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 5);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Ornithopter"); // an artifact creature is never sacrificed
        addCard(Zone.BATTLEFIELD, playerB, "Savannah Lions");
        addCard(Zone.HAND, playerB, "Island");
        addCard(Zone.HAND, playerA, confluence);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, confluence);
        setChoice(playerA, "X=2");
        setChoice(playerA, discard);
        setChoice(playerA, sacrifice);
        setChoice(playerA, "Grizzly Bears"); // own sacrifice
        setChoice(playerB, "Savannah Lions"); // the opponent's sacrifice
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, "Grizzly Bears", 1);
        assertPermanentCount(playerA, "Ornithopter", 1);
        assertGraveyardCount(playerB, "Savannah Lions", 1);
        assertGraveyardCount(playerB, "Island", 1);
    }

    @Test
    public void testXZeroDoesNothing() {
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Savannah Lions");
        addCard(Zone.HAND, playerA, confluence);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, confluence);
        setChoice(playerA, "X=0");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerB, "Savannah Lions", 1);
        assertGraveyardCount(playerA, confluence, 1);
    }
}
