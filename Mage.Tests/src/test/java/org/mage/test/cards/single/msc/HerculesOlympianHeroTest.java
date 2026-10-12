package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class HerculesOlympianHeroTest extends CardTestPlayerBase {

    @Test
    public void testAttackAndDamageCounters() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Hercules, Olympian Hero");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        attack(1, playerA, "Hercules, Olympian Hero", playerB);
        block(1, playerB, "Grizzly Bears", "Hercules, Olympian Hero");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertCounterCount(playerA, "Hercules, Olympian Hero", CounterType.P1P1, 3);
        assertPowerToughness(playerA, "Hercules, Olympian Hero", 6, 6);
    }
}
