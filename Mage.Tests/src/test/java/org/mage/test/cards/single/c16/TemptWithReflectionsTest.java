package org.mage.test.cards.single.c16;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommander4Players;

/**
 * Tempt with Reflections
 * {3}{U}
 * Sorcery
 * Tempting offer - Choose target creature you control. Create a token that's a copy of that creature.
 * Each opponent may create a token that's a copy of that creature. For each opponent who does,
 * create a token that's a copy of that creature.
 */
public class TemptWithReflectionsTest extends CardTestCommander4Players {

    private static final String tempt = "Tempt with Reflections";
    private static final String bears = "Grizzly Bears";

    @Test
    public void testEveryOpponentCopies() {
        setStrictChooseMode(true);

        addCard(Zone.HAND, playerA, tempt);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.BATTLEFIELD, playerA, bears);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, tempt, bears);
        setChoice(playerB, true);
        setChoice(playerC, true);
        setChoice(playerD, true);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // the original, a token for the caster and one more for each opponent who copied
        assertPermanentCount(playerA, bears, 1 + 1 + 3);
        assertPermanentCount(playerB, bears, 1);
        assertPermanentCount(playerC, bears, 1);
        assertPermanentCount(playerD, bears, 1);
    }

    @Test
    public void testOnlyOpponentsWhoSayYesCopy() {
        setStrictChooseMode(true);

        addCard(Zone.HAND, playerA, tempt);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.BATTLEFIELD, playerA, bears);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, tempt, bears);
        setChoice(playerB, false);
        setChoice(playerC, true);
        setChoice(playerD, false);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, bears, 1 + 1 + 1);
        assertPermanentCount(playerB, bears, 0);
        assertPermanentCount(playerC, bears, 1);
        assertPermanentCount(playerD, bears, 0);
    }
}
