package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class HeroicReturnTest extends CardTestPlayerBase {

    @Test
    public void testReducedAndHeroCounters() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Heroic Return");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.GRAVEYARD, playerA, "Hercules, Olympian Hero");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        attack(2, playerB, "Grizzly Bears", playerA);
        castSpell(2, PhaseStep.DECLARE_BLOCKERS, playerA, "Heroic Return", "Hercules, Olympian Hero");

        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Hercules, Olympian Hero", 1);
        assertCounterCount(playerA, "Hercules, Olympian Hero", CounterType.P1P1, 2);
    }
}
