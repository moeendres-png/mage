package org.mage.test.cards.single.zen;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class FeastOfBloodTest extends CardTestPlayerBase {

    private static final String FEAST = "Feast of Blood"; // {1}{B}

    @Test
    public void testTwoVampiresDestroyAndGainFour() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Child of Night", 2); // Vampire
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.HAND, playerA, FEAST);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, FEAST, "Grizzly Bears");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertLife(playerA, 20 + 4);
    }

    @Test
    public void testOneVampireCannotCast() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Child of Night", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.HAND, playerA, FEAST);

        checkPlayableAbility("one vampire", 1, PhaseStep.PRECOMBAT_MAIN, playerA, "Cast " + FEAST, false);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
