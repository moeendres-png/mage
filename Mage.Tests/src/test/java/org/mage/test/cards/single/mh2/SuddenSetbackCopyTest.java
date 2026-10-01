package org.mage.test.cards.single.mh2;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Sudden Setback: "The owner of target spell or nonland permanent puts it on the top or bottom of
 * their library."
 * <p>
 * Targeting a copy of a spell: the copy leaves the stack and ceases to exist (CR 707.10a). Sudden
 * Setback itself must still resolve normally and go to its owner's graveyard, and only the original
 * spell may resolve.
 */
public class SuddenSetbackCopyTest extends CardTestPlayerBase {

    @Test
    public void suddenSetbackOnACopyRemovesTheCopyAndGoesToTheGraveyard() {
        setStrictChooseMode(true);

        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.HAND, playerA, "Twincast");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.HAND, playerB, "Sudden Setback");
        addCard(Zone.BATTLEFIELD, playerB, "Island", 4);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", playerB);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Twincast", "Lightning Bolt", "Lightning Bolt", StackClause.WHILE_ON_STACK);
        setChoice(playerA, false); // Twincast: keep the copy's target
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, true); // only Twincast resolves; original + copy remain

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerB, "Sudden Setback", "Lightning Bolt[only copy]", "Lightning Bolt", StackClause.WHILE_ON_STACK);
        setChoice(playerA, true); // owner of the copy: top of library

        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerB, "Sudden Setback", 1);
        assertLibraryCount(playerB, "Sudden Setback", 0);
        assertLibraryCount(playerA, "Lightning Bolt", 0);
        assertLife(playerB, 20 - 3); // only the original Bolt resolves
        assertGraveyardCount(playerA, "Lightning Bolt", 1);
        assertGraveyardCount(playerA, "Twincast", 1);
    }

    @Test
    public void suddenSetbackOnTheOriginalPutsItOnTopOfItsOwnersLibrary() {
        setStrictChooseMode(true);

        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 1);
        addCard(Zone.HAND, playerB, "Sudden Setback");
        addCard(Zone.BATTLEFIELD, playerB, "Island", 4);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", playerB);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerB, "Sudden Setback", "Lightning Bolt", "Lightning Bolt", StackClause.WHILE_ON_STACK);
        setChoice(playerA, true); // owner: top of library

        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerB, "Sudden Setback", 1);
        assertLife(playerB, 20);
        assertGraveyardCount(playerA, "Lightning Bolt", 0);
        Assert.assertEquals("Lightning Bolt", playerA.getLibrary().getFromTop(currentGame).getName());
    }
}
