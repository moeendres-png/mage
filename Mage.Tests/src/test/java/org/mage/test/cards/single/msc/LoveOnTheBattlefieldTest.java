package org.mage.test.cards.single.msc;

import mage.abilities.keyword.FirstStrikeAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class LoveOnTheBattlefieldTest extends CardTestPlayerBase {

    @Test
    public void testExactlyTwoAttackers() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Love on the Battlefield");
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion");

        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Silvercoat Lion", playerB);
        // both delayed counter triggers fire in the first-strike damage step: order them
        setChoice(playerA, "Whenever either of those creatures deals combat damage");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertHandCount(playerA, 1);
        assertLife(playerB, 16);
        assertCounterCount(playerA, "Grizzly Bears", CounterType.P1P1, 1);
        assertCounterCount(playerA, "Silvercoat Lion", CounterType.P1P1, 1);
    }

    @Test
    public void testThreeAttackersNoTrigger() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Love on the Battlefield");
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion");
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant");

        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Silvercoat Lion", playerB);
        attack(1, playerA, "Hill Giant", playerB);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        // "exactly two": no draw, no first strike counters
        assertHandCount(playerA, 0);
        assertLife(playerB, 20 - 2 - 2 - 3);
        assertCounterCount(playerA, "Grizzly Bears", CounterType.P1P1, 0);
        assertAbility(playerA, "Grizzly Bears", FirstStrikeAbility.getInstance(), false);
    }
}
