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
public class StridingShotcallerTest extends CardTestPlayerBase {

    private static final String CARD = "Striding Shotcaller";

    private void assertPrepared(int turn, PhaseStep step, boolean expected) {
        runCode("prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> CARD.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, permanent.isPrepared());
        });
    }

    @Test
    public void testCombatDamagePrepares() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");

        assertPrepared(1, PhaseStep.DECLARE_ATTACKERS, false);
        attack(1, playerA, "Grizzly Bears", playerB);
        assertPrepared(1, PhaseStep.END_COMBAT, true);

        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void testBlockedNoDamageNoPrepare() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerB, "Wall of Stone");

        attack(3, playerA, "Grizzly Bears", playerB);
        block(3, playerB, "Wall of Stone", "Grizzly Bears");
        assertPrepared(3, PhaseStep.END_COMBAT, false);

        setStopAt(3, PhaseStep.END_TURN);
        execute();
    }
}
