package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * The Moment {2}
 * Legendary Artifact
 * At the beginning of your upkeep, put a time counter on The Moment.
 * {2}, {T}: Untap target creature you control. It phases out until The Moment leaves the battlefield.
 * {3}, {T}: Destroy each nonland permanent with mana value less than or equal to the number of time counters
 * on The Moment. Then sacrifice The Moment. Activate only as a sorcery.
 */
public class TheMomentTest extends CardTestPlayerBase {

    private static final String moment = "The Moment";
    private static final String bears = "Grizzly Bears"; // {1}{G}, MV 2

    @Test
    public void testUpkeepAddsATimeCounterOnYourTurnsOnly() {
        addCard(Zone.BATTLEFIELD, playerA, moment);

        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertCounterCount(moment, CounterType.TIME, 2); // upkeeps of turn 1 and turn 3, not turn 2
    }

    @Test
    public void testItPhasesOutUntilTheMomentLeavesAndUntaps() {
        addCard(Zone.BATTLEFIELD, playerA, moment);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.HAND, playerB, "Disenchant");
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 2);

        attack(1, playerA, bears);
        activateAbility(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "{2}, {T}: Untap target creature you control", bears);
        // the Bears do not phase in at their controller's next untap step (turn 3)
        checkPermanentCount("phased out", 3, PhaseStep.PRECOMBAT_MAIN, playerA, bears, 0);
        checkGraveyardCount("not dead", 3, PhaseStep.PRECOMBAT_MAIN, playerA, bears, 0);
        checkPermanentCount("The Moment stays", 3, PhaseStep.PRECOMBAT_MAIN, playerA, moment, 1);
        castSpell(4, PhaseStep.PRECOMBAT_MAIN, playerB, "Disenchant", moment);
        setStrictChooseMode(true);
        setStopAt(4, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, moment, 1);
        assertPermanentCount(playerA, bears, 1); // phased in the moment The Moment left
        assertTapped(bears, false); // it was untapped before it phased out
    }

    @Test
    public void testDestroysNonlandPermanentsUpToTheCounterCountAndSacrificesItself() {
        addCard(Zone.BATTLEFIELD, playerA, moment);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.BATTLEFIELD, playerA, bears); // MV 2: destroyed
        addCard(Zone.BATTLEFIELD, playerB, "Savannah Lions"); // MV 1: destroyed
        addCard(Zone.BATTLEFIELD, playerB, "Serra Angel"); // MV 5: survives
        addCard(Zone.BATTLEFIELD, playerB, "Island"); // land: survives

        activateAbility(3, PhaseStep.PRECOMBAT_MAIN, playerA, "{3}, {T}: Destroy each nonland permanent");
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, bears, 1);
        assertGraveyardCount(playerB, "Savannah Lions", 1);
        assertPermanentCount(playerB, "Serra Angel", 1);
        assertPermanentCount(playerB, "Island", 1);
        assertGraveyardCount(playerA, moment, 1);
    }

    @Test
    public void testItIsSorcerySpeed() {
        addCard(Zone.BATTLEFIELD, playerA, moment);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);

        checkPlayableAbility("not during combat", 1, PhaseStep.BEGIN_COMBAT, playerA, "{3}, {T}: Destroy each nonland permanent", false);
        checkPlayableAbility("main phase", 1, PhaseStep.PRECOMBAT_MAIN, playerA, "{3}, {T}: Destroy each nonland permanent", true);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }
}
