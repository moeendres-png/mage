package org.mage.test.cards.single.tmc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class DimensionXPizzasaurTest extends CardTestPlayerBase {

    private static final String PIZZASAUR = "Dimension X Pizzasaur";

    @Test
    public void testCountersThenDestroyByCounterCount() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, PIZZASAUR);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 4);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // MV 2 <= 2 counters
        addCard(Zone.BATTLEFIELD, playerB, "Hill Giant"); // MV 4: not destroyable

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, PIZZASAUR);
        addTarget(playerA, PIZZASAUR); // two +1/+1 counters on itself
        addTarget(playerA, "Grizzly Bears"); // reflexive: destroy MV <= 2

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertCounterCount(playerA, PIZZASAUR, CounterType.P1P1, 2);
        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertPermanentCount(playerB, "Hill Giant", 1);
    }

    @Test
    public void testSacrificeDrainsEachOpponent() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, PIZZASAUR);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}, Sacrifice");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, PIZZASAUR, 1);
        assertLife(playerA, 23);
        assertLife(playerB, 17);
    }
}
