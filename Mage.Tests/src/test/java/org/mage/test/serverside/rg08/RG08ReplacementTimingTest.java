package org.mage.test.serverside.rg08;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * RG-08 actual-card replacement/prevention timing qualification.
 */
public class RG08ReplacementTimingTest extends CardTestPlayerBase {

    @Test
    public void optionalDredgeDeclinedDoesNotLoopAndNormalDrawContinues() {
        addCard(Zone.GRAVEYARD, playerB, "Stinkweed Imp", 1);
        addCard(Zone.LIBRARY, playerB, "Silvercoat Lion", 6);
        skipInitShuffling();

        setChoice(playerB, false); // decline Dredge

        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerB, "Stinkweed Imp", 1);
        assertHandCount(playerB, "Stinkweed Imp", 0);
        assertHandCount(playerB, "Silvercoat Lion", 1);
    }

    @Test
    public void affectedControllerCanChooseSeasonBeforePir() {
        addCard(Zone.BATTLEFIELD, playerA, "Doubling Season", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Pir, Imaginative Rascal", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Chandra, Fire Artisan", 1);

        setChoice(playerA, "Doubling Season");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertCounterCount(playerA, "Chandra, Fire Artisan", CounterType.LOYALTY, 9);
    }

    @Test
    public void affectedControllerCanChoosePirBeforeSeasonAndApplicabilityRecomputes() {
        addCard(Zone.BATTLEFIELD, playerA, "Doubling Season", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Pir, Imaginative Rascal", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Chandra, Fire Artisan", 1);

        setChoice(playerA, "Pir, Imaginative Rascal");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertCounterCount(playerA, "Chandra, Fire Artisan", CounterType.LOYALTY, 10);
    }

    @Test
    public void sameReplacementDoesNotApplyTwiceToSameEvent() {
        addCard(Zone.BATTLEFIELD, playerA, "Doubling Season", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.HAND, playerA, "Pallid Mycoderm", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Pallid Mycoderm");

        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertCounterCount("Pallid Mycoderm", CounterType.SPORE, 2);
    }

    @Test
    public void damageReplacementThenPreventionUsesModifiedDamageEvent() {
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.HAND, playerA, "Test of Faith", 1);

        addCard(Zone.BATTLEFIELD, playerB, "Furnace of Rath", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Mountain", 1);
        addCard(Zone.HAND, playerB, "Shock", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Test of Faith", "Silvercoat Lion");
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerB, "Shock", "Silvercoat Lion");
        setChoice(playerA, "Furnace of Rath");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Silvercoat Lion", 1);
        assertCounterCount("Silvercoat Lion", CounterType.P1P1, 3);
        assertDamageReceived(playerA, "Silvercoat Lion", 1);
    }

    @Test
    public void multiObjectDestroyConsumesZoneReplacementForEachObject() {
        addCard(Zone.BATTLEFIELD, playerA, "Rest in Peace", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.HAND, playerA, "Wrath of God", 1);

        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Wrath of God");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerB, 0);
        assertGraveyardCount(playerB, "Grizzly Bears", 0);
        assertGraveyardCount(playerB, "Silvercoat Lion", 0);
        assertExileCount(playerB, "Grizzly Bears", 1);
        assertExileCount(playerB, "Silvercoat Lion", 1);
    }

    @Test
    public void dredgeReplacementFeedsModifiedContinuationNotStaleDraw() {
        addCard(Zone.GRAVEYARD, playerB, "Stinkweed Imp", 1);
        addCard(Zone.LIBRARY, playerB, "Silvercoat Lion", 5);
        skipInitShuffling();

        setChoice(playerB, true); // apply Dredge 5

        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertHandCount(playerB, "Stinkweed Imp", 1);
        assertHandCount(playerB, "Silvercoat Lion", 0);
        assertGraveyardCount(playerB, "Silvercoat Lion", 5);
    }
}
