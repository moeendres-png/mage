package org.mage.test.cards.single.msc;

import mage.abilities.keyword.FlyingAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Storm, Queen of Wakanda {3}{G}{W}
 * Legendary Creature — Mutant Noble Hero 4/5
 * Flying
 * Whenever Storm attacks, until end of turn, another target attacking creature gains flying and gets +X/+0,
 * where X is Storm's power.
 * Whenever a creature with flying attacks you, Storm deals damage equal to her power to that creature.
 *
 * @author commander-lab
 */
public class StormQueenOfWakandaTest extends CardTestPlayerBase {

    private static final String STORM = "Storm, Queen of Wakanda";
    private static final String BEARS = "Grizzly Bears";

    @Test
    public void testAttackingCompanionGainsFlyingAndStormsPower() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, STORM);
        addCard(Zone.BATTLEFIELD, playerA, BEARS);

        attack(1, playerA, STORM, playerB);
        attack(1, playerA, BEARS, playerB);
        addTarget(playerA, BEARS);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertAbilityCount(playerA, BEARS, FlyingAbility.class, 1);
        assertPowerToughness(playerA, BEARS, 6, 2); // +4/+0 (Storm's power)
        assertLife(playerB, 20 - 4 - 6);
    }

    @Test
    public void testBoostIsStormsPowerNotAConstant() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, STORM);
        addCard(Zone.BATTLEFIELD, playerA, BEARS);
        addCard(Zone.BATTLEFIELD, playerA, "Glorious Anthem"); // Storm is 5/6 now

        attack(1, playerA, STORM, playerB);
        attack(1, playerA, BEARS, playerB);
        addTarget(playerA, BEARS);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertPowerToughness(playerA, BEARS, 8, 3); // 3/3 from the anthem + 5 from Storm
        assertLife(playerB, 20 - 5 - 8);
    }

    @Test
    public void testStormAttackingAloneBoostsNothing() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, STORM);

        attack(1, playerA, STORM, playerB);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        // no other attacking creature, so the trigger has no legal target and never resolves
        assertLife(playerB, 20 - 4);
    }

    @Test
    public void testFlyingCreatureAttackingYouTakesStormsPower() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, STORM);
        addCard(Zone.BATTLEFIELD, playerB, "Shivan Dragon"); // 5/5 flying

        attack(2, playerB, "Shivan Dragon", playerA);

        setStopAt(2, PhaseStep.END_COMBAT);
        execute();

        Assert.assertEquals(4, getPermanent("Shivan Dragon").getDamage());
        assertLife(playerA, 20 - 5); // its combat damage still gets through
    }

    @Test
    public void testNonFlyingCreatureAttackingYouTakesNoDamage() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, STORM);
        addCard(Zone.BATTLEFIELD, playerB, "Craw Wurm"); // 6/4, no flying

        attack(2, playerB, "Craw Wurm", playerA);

        setStopAt(2, PhaseStep.END_COMBAT);
        execute();

        Assert.assertEquals(0, getPermanent("Craw Wurm").getDamage());
        assertLife(playerA, 20 - 6);
    }

    @Test
    public void testFlyingCreatureYouControlAttackingAnOpponentHitsNoOne() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, STORM);
        addCard(Zone.BATTLEFIELD, playerA, "Shivan Dragon"); // 5/5 flying of our own

        attack(1, playerA, "Shivan Dragon", playerB);
        attack(1, playerA, STORM, playerB); // Storm attacks too, so it also has a legal target
        addTarget(playerA, "Shivan Dragon");

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        // the watcher only cares about creatures with flying attacking *you*
        Assert.assertEquals(0, getPermanent("Shivan Dragon").getDamage());
        assertPowerToughness(playerA, "Shivan Dragon", 9, 5); // Storm still pumps her
        assertLife(playerB, 20 - 4 - 9);
    }
}
