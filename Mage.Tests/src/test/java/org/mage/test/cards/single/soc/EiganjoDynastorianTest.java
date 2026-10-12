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
public class EiganjoDynastorianTest extends CardTestPlayerBase {

    private static final String EIGANJO = "Eiganjo Dynastorian";

    private void assertPrepared(int turn, PhaseStep step, boolean expected) {
        runCode("prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> EIGANJO.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, permanent.isPrepared());
        });
    }

    @Test
    public void testTwoAttackersPrepareAndReplenishReturnsEnchantments() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, EIGANJO);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.GRAVEYARD, playerA, "Pacifism");
        addCard(Zone.GRAVEYARD, playerA, "Glorious Anthem");

        attack(1, playerA, EIGANJO, playerB);
        attack(1, playerA, "Grizzly Bears", playerB);
        assertPrepared(1, PhaseStep.END_COMBAT, true);

        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Replenish");
        setChoice(playerA, EIGANJO); // Pacifism returns attached: enchant a creature

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Glorious Anthem", 1);
        assertPermanentCount(playerA, "Pacifism", 1);
    }

    @Test
    public void testOneAttackerDoesNotPrepare() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, EIGANJO);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");

        attack(1, playerA, EIGANJO, playerB);
        assertPrepared(1, PhaseStep.END_COMBAT, false);

        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }
}
