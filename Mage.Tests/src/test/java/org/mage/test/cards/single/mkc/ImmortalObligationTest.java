package org.mage.test.cards.single.mkc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Immortal Obligation {1}{W} instant
 * Return target creature card from an opponent's graveyard to the battlefield under their control with a duty
 * counter on it. For as long as that creature has a duty counter on it, it is goaded, can't attack you or a
 * permanent you control, and can't block creatures you control.
 */
public class ImmortalObligationTest extends CardTestPlayerBase {

    private static final String obligation = "Immortal Obligation";
    private static final String bears = "Grizzly Bears";
    private static final String lions = "Savannah Lions";

    @Test
    public void testReturnsUnderTheirControlWithADutyCounterAndGoadsIt() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.GRAVEYARD, playerB, bears);
        addCard(Zone.HAND, playerA, obligation);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, obligation, bears);
        runCode("goaded by the caster", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents().stream()
                    .filter(p -> p.getName().equals(bears)).findFirst().orElse(null);
            Assert.assertNotNull(permanent);
            Assert.assertTrue(permanent.getGoadingPlayers().contains(playerA.getId()));
        });
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerB, bears, 1);
        assertGraveyardCount(playerB, bears, 0);
        assertCounterCount(playerB, bears, CounterType.DUTY, 1);
    }

    @Test
    public void testItCannotAttackTheCaster() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.GRAVEYARD, playerB, bears);
        addCard(Zone.HAND, playerA, obligation);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, obligation, bears);
        runCode("cannot attack the caster", 2, PhaseStep.BEGIN_COMBAT, playerB, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents().stream()
                    .filter(p -> p.getName().equals(bears)).findFirst().orElse(null);
            Assert.assertNotNull(permanent);
            Assert.assertFalse(permanent.canAttack(playerA.getId(), game));
        });
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertCounterCount(playerB, bears, CounterType.DUTY, 1);
    }

    @Test
    public void testItCannotBlockTheCastersCreatures() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, lions);
        addCard(Zone.GRAVEYARD, playerB, bears);
        addCard(Zone.HAND, playerA, obligation);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, obligation, bears);
        attack(3, playerA, lions);
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 18); // the returned Bears could have blocked the 2/1 Lions otherwise
        assertGraveyardCount(playerA, lions, 0);
    }

    @Test
    public void testWithoutTheDutyCounterItBlocksAgain() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, lions);
        addCard(Zone.GRAVEYARD, playerB, bears);
        addCard(Zone.HAND, playerA, obligation);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, obligation, bears);
        runCode("remove the duty counter", 3, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents().stream()
                    .filter(p -> p.getName().equals(bears)).findFirst().orElse(null);
            Assert.assertNotNull(permanent);
            permanent.removeCounters(CounterType.DUTY.getName(), 1, null, game);
        });
        attack(3, playerA, lions);
        block(3, playerB, bears, lions);
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20);
        assertGraveyardCount(playerA, lions, 1);
    }
}
