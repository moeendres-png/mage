package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class TheFrightfulFourTest extends CardTestPlayerBase {

    @Test
    public void testOnlyTheFirstNoncreatureSpellEachTurn() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "The Frightful Four");
        addCard(Zone.BATTLEFIELD, playerB, "Forest", 4);
        addCard(Zone.HAND, playerB, "Llanowar Elves"); // creature spell: no loss
        addCard(Zone.HAND, playerB, "Giant Growth", 2); // MV 1 each, only the first counts

        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Llanowar Elves");
        waitStackResolved(2, PhaseStep.PRECOMBAT_MAIN);
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Giant Growth", "Llanowar Elves");
        waitStackResolved(2, PhaseStep.PRECOMBAT_MAIN);
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Giant Growth", "Llanowar Elves");

        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertLife(playerB, 20 - 1);
    }

    @Test
    public void testOwnSpellsDoNotCount() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "The Frightful Four");
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.HAND, playerA, "Giant Growth");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Giant Growth", "The Frightful Four");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertLife(playerA, 20);
    }
}
