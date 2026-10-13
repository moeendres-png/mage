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
public class InspiredSkypainterTest extends CardTestPlayerBase {

    private static final String CARD = "Inspired Skypainter";

    private void assertPrepared(int turn, PhaseStep step, boolean expected) {
        runCode("prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> CARD.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, permanent.isPrepared());
        });
    }

    @Test
    public void testEntersPrepared() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Volcanic Island", 2);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, CARD);
        assertPrepared(1, PhaseStep.POSTCOMBAT_MAIN, true);

        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void testNonTokenDamageDoesNotPrepare() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD); // on the battlefield from the start: no ETB
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");

        attack(1, playerA, "Grizzly Bears", playerB);
        assertPrepared(1, PhaseStep.END_COMBAT, false);

        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }
}
