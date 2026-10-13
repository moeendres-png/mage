package org.mage.test.cards.single.msc;

import mage.abilities.keyword.DoubleStrikeAbility;
import mage.abilities.keyword.TrampleAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Okoye, Mighty and Adored {2}{G}{W}
 * Legendary Creature — Human Warrior Hero 3/3
 * When Okoye enters, you become the monarch.
 * At the beginning of combat on your turn, put a +1/+1 counter on target creature. Whenever that creature
 * attacks the monarch this turn, it gains double strike and trample until end of turn.
 *
 * @author commander-lab
 */
public class OkoyeMightyAndAdoredTest extends CardTestPlayerBase {

    private static final String OKOYE = "Okoye, Mighty and Adored";
    private static final String BEARS = "Grizzly Bears";

    @Test
    public void testEntersMakesYouMonarch() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, OKOYE);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Plains");
        addCard(Zone.BATTLEFIELD, playerA, BEARS); // the beginning of combat target

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, OKOYE);
        addTarget(playerA, BEARS);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, OKOYE, 1);
        Assert.assertEquals(playerA.getId(), currentGame.getMonarchId());
    }

    @Test
    public void testCountedCreatureAttackingTheMonarchGainsDoubleStrikeAndTrample() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, OKOYE);
        addCard(Zone.BATTLEFIELD, playerA, BEARS);
        runCode("PlayerB is the monarch", 1, PhaseStep.UPKEEP, playerA,
                (info, player, game) -> game.setMonarchId(null, playerB.getId()));

        addTarget(playerA, BEARS); // beginning of combat: target creature gets the counter
        attack(1, playerA, BEARS, playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertCounterCount(playerA, BEARS, CounterType.P1P1, 1);
        assertPowerToughness(playerA, BEARS, 3, 3);
        assertAbilityCount(playerA, BEARS, DoubleStrikeAbility.class, 1);
        assertAbilityCount(playerA, BEARS, TrampleAbility.class, 1);
        assertLife(playerB, 20 - 3 - 3); // double strike
    }

    @Test
    public void testCountedCreatureAttackingANonMonarchGainsNoDoubleStrike() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, OKOYE);
        addCard(Zone.BATTLEFIELD, playerA, BEARS);
        runCode("PlayerA is the monarch", 1, PhaseStep.UPKEEP, playerA,
                (info, player, game) -> game.setMonarchId(null, playerA.getId()));

        addTarget(playerA, BEARS); // beginning of combat: target creature gets the counter
        attack(1, playerA, BEARS, playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertCounterCount(playerA, BEARS, CounterType.P1P1, 1);
        assertPowerToughness(playerA, BEARS, 3, 3);
        assertAbilityCount(playerA, BEARS, DoubleStrikeAbility.class, 0);
        assertAbilityCount(playerA, BEARS, TrampleAbility.class, 0);
        assertLife(playerB, 20 - 3);
    }

    @Test
    public void testUncountedCreatureAttackingTheMonarchGainsNoDoubleStrike() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, OKOYE);
        addCard(Zone.BATTLEFIELD, playerA, BEARS);
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant");
        runCode("PlayerB is the monarch", 1, PhaseStep.UPKEEP, playerA,
                (info, player, game) -> game.setMonarchId(null, playerB.getId()));

        addTarget(playerA, "Hill Giant"); // counter on Hill Giant, not on the attacker
        attack(1, playerA, BEARS, playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertCounterCount(playerA, BEARS, CounterType.P1P1, 0);
        assertAbilityCount(playerA, BEARS, DoubleStrikeAbility.class, 0);
        assertAbilityCount(playerA, BEARS, TrampleAbility.class, 0);
        assertLife(playerB, 20 - 2);
    }
}
