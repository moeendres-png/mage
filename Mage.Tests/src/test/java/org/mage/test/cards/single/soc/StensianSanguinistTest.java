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
public class StensianSanguinistTest extends CardTestPlayerBase {

    private static final String CARD = "Stensian Sanguinist";

    private void assertPrepared(int turn, PhaseStep step, boolean expected) {
        runCode("prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> CARD.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, permanent.isPrepared());
        });
    }

    @Test
    public void testDeathtouchCreatureDealsDamageAndPrepares() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");

        attack(1, playerA, "Grizzly Bears", playerB);
        addTarget(playerA, "Grizzly Bears"); // gains deathtouch
        assertPrepared(1, PhaseStep.END_COMBAT, true);

        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void testOtherCreatureDamageDoesNotPrepare() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant");

        attack(1, playerA, "Grizzly Bears", playerB);
        addTarget(playerA, "Hill Giant"); // not attacking: never deals combat damage
        assertPrepared(1, PhaseStep.END_COMBAT, false);

        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void testExsanguinateFromPreparedCopy() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 4);

        attack(1, playerA, "Grizzly Bears", playerB);
        addTarget(playerA, "Grizzly Bears");
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Exsanguinate");
        setChoiceAmount(playerA, 2); // X = 2

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 2 - 2);
        assertLife(playerA, 20 + 2);
    }
}
