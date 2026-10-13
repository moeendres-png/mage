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
public class EccentricPestfinderTest extends CardTestPlayerBase {

    private static final String CARD = "Eccentric Pestfinder";

    private void assertPrepared(int turn, PhaseStep step, boolean expected) {
        runCode("prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> CARD.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, permanent.isPrepared());
        });
    }

    @Test
    public void testLifeGainPreparesAndTurnStonesMakesPests() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Bayou", 2);
        addCard(Zone.HAND, playerA, "Revitalize"); // {1}{W}: gain 3 life, draw a card

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Revitalize");
        assertPrepared(2, PhaseStep.UPKEEP, true);
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Turn Stones");
        assertPrepared(3, PhaseStep.POSTCOMBAT_MAIN, false);

        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Pest Token", 1);
    }

    @Test
    public void testNoLifeGainNoPrepare() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, CARD);
        assertPrepared(2, PhaseStep.UPKEEP, false);

        setStopAt(2, PhaseStep.DRAW);
        execute();
    }
}
