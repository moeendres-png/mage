package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class BatrocTheLeaperTest extends CardTestPlayerBase {

    private static final String BATROC = "Batroc the Leaper";

    @Test
    public void testKickedTwice() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, BATROC);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 6);
        addCard(Zone.BATTLEFIELD, playerB, "Hill Giant");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, BATROC);
        setChoice(playerA, true); // multikicker once
        setChoice(playerA, true); // twice
        setChoice(playerA, false); // stop
        addTarget(playerA, playerB);
        addTarget(playerA, "Hill Giant");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertCounterCount(playerA, BATROC, CounterType.P1P1, 2);
        assertPowerToughness(playerA, BATROC, 4, 4);
        assertLife(playerB, 20 - 4);
        assertGraveyardCount(playerB, "Hill Giant", 1);
    }

    @Test
    public void testUnkicked() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, BATROC);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 2);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, BATROC);
        setChoice(playerA, false); // no multikicker: up to zero targets, no damage

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPowerToughness(playerA, BATROC, 2, 2);
        assertLife(playerB, 20);
    }
}
