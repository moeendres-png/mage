package org.mage.test.cards.single.msc;

import mage.abilities.keyword.TrampleAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class MBakuJabariChieftainTest extends CardTestPlayerBase {

    private static final String MBAKU = "M'Baku, Jabari Chieftain";

    @Test
    public void testEndStepMakesOpponentMonarch() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, MBAKU);
        addTarget(playerA, playerB); // no monarch yet: the end-step trigger names PlayerB

        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        Assert.assertEquals(playerB.getId(), currentGame.getMonarchId());
    }

    @Test
    public void testAttackingTheMonarchGetsBoostAndTrample() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, MBAKU);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        runCode("PlayerB is the monarch", 1, PhaseStep.UPKEEP, playerA,
                (info, player, game) -> game.setMonarchId(null, playerB.getId()));
        attack(1, playerA, "Grizzly Bears", playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20 - 3);
        assertAbility(playerA, "Grizzly Bears", TrampleAbility.getInstance(), true);
    }

    @Test
    public void testAttackingANonMonarchNoBoost() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, MBAKU);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        runCode("PlayerA is the monarch", 1, PhaseStep.UPKEEP, playerA,
                (info, player, game) -> game.setMonarchId(null, playerA.getId()));
        attack(1, playerA, "Grizzly Bears", playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20 - 2);
        assertAbility(playerA, "Grizzly Bears", TrampleAbility.getInstance(), false);
    }
}
