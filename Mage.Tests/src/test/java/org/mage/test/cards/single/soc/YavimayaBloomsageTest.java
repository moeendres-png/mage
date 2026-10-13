package org.mage.test.cards.single.soc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class YavimayaBloomsageTest extends CardTestPlayerBase {

    private static final String CARD = "Yavimaya Bloomsage";

    private void assertPrepared(int turn, PhaseStep step, boolean expected) {
        runCode("prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> CARD.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, permanent.isPrepared());
        });
    }

    @Test
    public void testPowerSevenPrepares() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Craw Wurm"); // 6/4 -> 7/5 with the counter

        addTarget(playerA, "Craw Wurm");
        assertPrepared(2, PhaseStep.UPKEEP, true);

        setStopAt(2, PhaseStep.DRAW);
        execute();
    }

    @Test
    public void testToughnessSevenDoesNotPrepare() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Wall of Stone"); // 0/8 -> 1/9: power 1

        addTarget(playerA, "Wall of Stone");
        assertPrepared(2, PhaseStep.UPKEEP, false);

        setStopAt(2, PhaseStep.DRAW);
        execute();
    }
}
