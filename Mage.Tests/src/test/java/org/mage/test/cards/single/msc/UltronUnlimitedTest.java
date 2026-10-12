package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class UltronUnlimitedTest extends CardTestPlayerBase {

    @Test
    public void testConniveTriggersVillainsAndPlan() {
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, "Ultron, Unlimited");
        addCard(Zone.BATTLEFIELD, playerA, "Iron Monger, Sadistic Tycoon");
        addCard(Zone.BATTLEFIELD, playerA, "Glorious Purpose");
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.LIBRARY, playerA, "Island");

        attack(1, playerA, "Ultron, Unlimited", playerB);
        setChoice(playerA, "Lightning Bolt"); // connive discard (nonland)
        setChoice(playerA, true); // pay {1} for a Robot Villain

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertGraveyardCount(playerA, "Lightning Bolt", 1);
        assertCounterCount(playerA, "Glorious Purpose", CounterType.PLAN, 1);
        assertCounterCount(playerA, "Iron Monger, Sadistic Tycoon", CounterType.P1P1, 1);
        // connive + Glorious Purpose + Iron Monger
        assertCounterCount(playerA, "Ultron, Unlimited", CounterType.P1P1, 3);
        assertPermanentCount(playerA, "Robot Villain Token", 1);
    }
}
