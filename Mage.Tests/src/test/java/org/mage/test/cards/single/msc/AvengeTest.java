package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class AvengeTest extends CardTestPlayerBase {

    @Test
    public void testCostReductionAndWipe() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Avenge");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        attack(2, playerB, "Grizzly Bears", playerA);
        // only four lands: castable only with the {2} reduction
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Avenge");

        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertGraveyardCount(playerA, "Avenge", 1);
        assertPermanentCount(playerA, "Silvercoat Lion", 0);
        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertLife(playerA, 20 - 2 + 2);
    }

    @Test
    public void testNoReductionWithoutAttack() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Avenge");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);

        checkPlayableAbility("not castable", 3, PhaseStep.PRECOMBAT_MAIN, playerA, "Cast Avenge", false);

        setStopAt(3, PhaseStep.END_TURN);
        execute();
    }
}
