package org.mage.test.serverside.ws81;

import mage.constants.PhaseStep;
import mage.constants.SubType;
import mage.constants.Zone;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * WS81 corrected H01 requalification (engine-direct, actual cards).
 *
 * Authority: CPL WS79 H01_CORRECTED_CASES.json at ee4d6297 (binding).
 * Old RQ-C3 copy-choice expectation under pre-existing Humility is SUPERSEDED.
 *
 * Decision-occurrence discrimination relies on strict choose mode:
 * - strict mode ON with NO preset choice: any offered copy decision (chooseUse
 *   and/or copy target) fails the test with "Missing CHOICE def" -- that
 *   failure is the FAIL evidence for H01-A (a decision occurred).
 * - strict mode ON with preset Yes + target: the run only passes if the
 *   engine actually consumed both decisions -- consumption is verified by
 *   assertAllCommandsUsed (unused choices fail). That is the occurrence
 *   evidence for H01-B / H01-C.
 *
 * Post-Humility discrimination: Humility is removed via Disenchant (a
 * legitimate spell, no Clone rewrite). H01-A must then be 0/0 -> SBA
 * graveyard; H01-B must remain a 2/2 Bear copy.
 *
 * No production code is touched by these tests.
 */
public class WS81H01CorrectedTest extends CardTestPlayerBase {

    /**
     * H01-A HUMILITY_FIRST: Humility pre-exists, Clone enters afterwards.
     * Correct: zero copy decisions, Clone enters as itself (1/1, no abilities
     * under Humility), then 0/0 -> graveyard by SBA once Humility leaves.
     */
    @Test
    public void testA_HumilityFirst_NoCopyDecision_CloneDiesAfterHumilityLeaves() {
        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Humility", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.HAND, playerA, "Clone", 1);
        addCard(Zone.HAND, playerA, "Disenchant", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Clone");
        // Intentionally NO setChoice: correct H01-A offers zero copy decisions.
        // Strict mode turns any offered decision into a hard failure
        // ("Missing CHOICE def"), which is the FAIL evidence.

        checkPT("H01-A: Clone is 1/1 under Humility", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Clone", 1, 1);

        runCode("H01-A under-Humility probe", 1, PhaseStep.POSTCOMBAT_MAIN, playerA,
                (info, p, g) -> {
                    Permanent clone = null;
                    for (Permanent perm : g.getBattlefield().getAllActivePermanents(p.getId())) {
                        if (perm.getName().equals("Clone")) {
                            clone = perm;
                            break;
                        }
                    }
                    Assert.assertNotNull("H01-A: Clone must be on the battlefield as itself under Humility", clone);
                    Assert.assertFalse("H01-A: Clone must NOT be a copy (no copy decision may occur)", clone.isCopy());
                    Assert.assertFalse("H01-A: Clone must NOT have Bear subtype",
                            clone.hasSubtype(SubType.BEAR, g));
                    Assert.assertTrue("H01-A: Clone must keep Shapeshifter subtype",
                            clone.hasSubtype(SubType.SHAPESHIFTER, g));
                    Assert.assertEquals("H01-A: Clone power under Humility", 1, clone.getPower().getValue());
                    Assert.assertEquals("H01-A: Clone toughness under Humility", 1, clone.getToughness().getValue());
                    Assert.assertTrue("H01-A: Clone must have no abilities under Humility",
                            clone.getAbilities(g).isEmpty());
                });

        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Disenchant", "Humility");

        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        // Post-Humility discriminator: Clone returns to printed 0/0 and dies to SBA 704.5f.
        assertPermanentCount(playerA, "Clone", 0);
        assertGraveyardCount(playerA, "Clone", 1);
        assertGraveyardCount(playerA, "Disenchant", 1);
        assertPermanentCount(playerB, "Humility", 0);
        // Original Bear restores to 2/2 once Humility leaves.
        assertPowerToughness(playerB, "Runeclaw Bear", 2, 2);
    }

    /**
     * H01-B CLONE_FIRST: Clone copies Bear first, Humility arrives later, then
     * leaves. Correct: copy decision occurs, Bear identity established, 1/1
     * under Humility, 2/2 Bear copy after Humility leaves.
     */
    @Test
    public void testB_CloneFirst_RetainsBearCopyAfterHumilityLeaves() {
        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.HAND, playerA, "Clone", 1);
        addCard(Zone.HAND, playerA, "Disenchant", 1);

        addCard(Zone.BATTLEFIELD, playerB, "Plains", 4);
        addCard(Zone.HAND, playerB, "Humility", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Clone");
        setChoice(playerA, true); // Yes: use the "enter as a copy" replacement
        setChoice(playerA, "Runeclaw Bear");

        runCode("H01-B pre-Humility probe", 1, PhaseStep.POSTCOMBAT_MAIN, playerA,
                (info, p, g) -> {
                    Permanent copy = null;
                    for (Permanent perm : g.getBattlefield().getAllActivePermanents(p.getId())) {
                        if (perm.getName().equals("Runeclaw Bear")) {
                            copy = perm;
                            break;
                        }
                    }
                    Assert.assertNotNull("H01-B: Bear copy must exist before Humility", copy);
                    Assert.assertTrue("H01-B: copy effect must be established", copy.isCopy());
                    Assert.assertTrue("H01-B: copy must have Bear subtype",
                            copy.hasSubtype(SubType.BEAR, g));
                    Assert.assertEquals("H01-B: copy power before Humility", 2, copy.getPower().getValue());
                    Assert.assertEquals("H01-B: copy toughness before Humility", 2, copy.getToughness().getValue());
                });

        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Humility");

        checkPT("H01-B: Bear copy is 1/1 under Humility", 2, PhaseStep.POSTCOMBAT_MAIN, playerA, "Runeclaw Bear", 1, 1);

        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Disenchant", "Humility");

        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        // Post-Humility discriminator: Bear-copy identity retained, back to 2/2.
        assertPermanentCount(playerA, "Runeclaw Bear", 1);
        assertPermanentCount(playerB, "Runeclaw Bear", 1);
        assertPowerToughness(playerA, "Runeclaw Bear", 2, 2);
        assertPowerToughness(playerB, "Runeclaw Bear", 2, 2);

        Permanent copy = getPermanent("Runeclaw Bear", playerA);
        Assert.assertNotNull("H01-B: playerA Bear copy must remain", copy);
        Assert.assertTrue("H01-B: Bear-copy identity must survive Humility leaving", copy.isCopy());
        Assert.assertTrue("H01-B: copy must be Bear subtype",
                copy.hasSubtype(SubType.BEAR, currentGame));
    }

    /**
     * H01-C NO_HUMILITY: normal Clone copy, no Humility involved.
     */
    @Test
    public void testC_NoHumility_NormalBearCopy() {
        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.HAND, playerA, "Clone", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Clone");
        setChoice(playerA, true); // Yes: use the "enter as a copy" replacement
        setChoice(playerA, "Runeclaw Bear");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Runeclaw Bear", 1);
        assertPermanentCount(playerB, "Runeclaw Bear", 1);
        assertPowerToughness(playerA, "Runeclaw Bear", 2, 2);

        Permanent copy = getPermanent("Runeclaw Bear", playerA);
        Assert.assertNotNull("H01-C: Bear copy must exist", copy);
        Assert.assertTrue("H01-C: copy effect must be established", copy.isCopy());
        Assert.assertTrue("H01-C: copy must be Bear subtype",
                copy.hasSubtype(SubType.BEAR, currentGame));
    }
}
