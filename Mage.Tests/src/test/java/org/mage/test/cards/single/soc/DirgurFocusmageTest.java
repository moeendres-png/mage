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
public class DirgurFocusmageTest extends CardTestPlayerBase {

    private static final String CARD = "Dirgur Focusmage";

    private void assertPrepared(int turn, PhaseStep step, boolean expected) {
        runCode("prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> CARD.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, permanent.isPrepared());
        });
    }

    @Test
    public void testInstantCostsOneLess() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.HAND, playerA, "Divination"); // {2}{U} -> {1}{U}
        addCard(Zone.BATTLEFIELD, playerA, "Island");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Divination");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, "Divination", 1);
        assertHandCount(playerA, 1 + 2);
    }

    @Test
    public void testBigSpellFromHandPrepares() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 5);
        addCard(Zone.HAND, playerA, "Sleep"); // {2}{U}{U} sorcery, MV 4: too small
        addCard(Zone.HAND, playerA, "Tidings"); // {3}{U}{U} sorcery, MV 5

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Sleep", playerB);
        assertPrepared(1, PhaseStep.POSTCOMBAT_MAIN, false);
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Tidings");
        assertPrepared(3, PhaseStep.POSTCOMBAT_MAIN, true);

        setStopAt(3, PhaseStep.END_TURN);
        execute();
    }
}
