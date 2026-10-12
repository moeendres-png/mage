package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class KangDynastyTest extends CardTestPlayerBase {

    @Test
    public void testTapGoadAndDraw() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Kang Dynasty");
        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Kang Dynasty");
        addTarget(playerA, "Grizzly Bears");

        // goaded Bears must attack on turn 2 and deal combat damage: Kang's controller draws
        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertLife(playerA, 18);
        assertHandCount(playerA, 1);
    }
}
