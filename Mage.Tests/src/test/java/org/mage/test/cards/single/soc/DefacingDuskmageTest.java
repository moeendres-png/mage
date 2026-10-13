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
public class DefacingDuskmageTest extends CardTestPlayerBase {

    private static final String DUSKMAGE = "Defacing Duskmage";

    private void assertPrepared(String name, int turn, PhaseStep step, boolean expected) {
        runCode(name + " prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent duskmage = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> DUSKMAGE.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, duskmage.isPrepared());
        });
    }

    @Test
    public void testOpponentsSecondDrawPreparesAndCopyCanBeCast() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, DUSKMAGE);
        addCard(Zone.BATTLEFIELD, playerA, "Plains");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);
        addCard(Zone.BATTLEFIELD, playerB, "Island", 3);
        addCard(Zone.HAND, playerB, "Divination");

        // turn 2: PlayerB's draw step is the first draw, Divination draws the second (and third)
        assertPrepared(DUSKMAGE, 2, PhaseStep.UPKEEP, false);
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Divination");
        assertPrepared(DUSKMAGE, 2, PhaseStep.BEGIN_COMBAT, true);

        // turn 3: cast the prepared copy of Vandal's Edit
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Vandal's Edit");
        assertPrepared(DUSKMAGE, 3, PhaseStep.BEGIN_COMBAT, false);

        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertLife(playerA, 18);
        assertLife(playerB, 18);
    }

    @Test
    public void testOneDrawDoesNotPrepare() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, DUSKMAGE);

        assertPrepared(DUSKMAGE, 2, PhaseStep.END_TURN, false);

        setStopAt(2, PhaseStep.CLEANUP);
        execute();
    }
}
