package org.mage.test.serverside.ws83;

import mage.constants.PhaseStep;
import mage.constants.SubType;
import mage.constants.Zone;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * WS83 systemic CR 614.12 coverage (actual cards, same general as-enters machinery).
 *
 * <p>Proves the ContinuousEffects entry-applicability repair is systemic rather than
 * Clone-specific, and that it respects each remover's own filter (no blanket suppression):
 * - Phantasmal Image (EntersBattlefieldAbility + CopyPermanentEffect, printed 0/0) under
 *   pre-existing Humility: zero copy decisions, enters as itself 1/1, then 0/0 -&gt; SBA.
 * - Vesuva (EntersBattlefieldAbility + CopyPermanentEffect, land) under pre-existing Humility:
 *   copy decision still occurs (Humility affects creatures only).
 * - Clone under pre-existing Dress Down (generic LoseAllAbilitiesAllEffect for creatures):
 *   zero copy decisions, enters as itself 0/0 -&gt; SBA (different remover class, same boundary).
 */
public class WS83CR61412SystemicTest extends CardTestPlayerBase {

    @Test
    public void testPhantasmalImageHumilityFirst_NoCopyDecision_DiesAfterHumilityLeaves() {
        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Humility", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 3);
        addCard(Zone.HAND, playerA, "Phantasmal Image", 1);
        addCard(Zone.HAND, playerA, "Disenchant", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Phantasmal Image");
        // No setChoice: correct behavior offers zero copy decisions under Humility.

        checkPT("Image is 1/1 under Humility", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Phantasmal Image", 1, 1);

        runCode("Image under-Humility probe", 1, PhaseStep.POSTCOMBAT_MAIN, playerA,
                (info, p, g) -> {
                    Permanent image = null;
                    for (Permanent perm : g.getBattlefield().getAllActivePermanents(p.getId())) {
                        if (perm.getName().equals("Phantasmal Image")) {
                            image = perm;
                            break;
                        }
                    }
                    Assert.assertNotNull("Image must be on battlefield as itself", image);
                    Assert.assertFalse("Image must NOT be a copy", image.isCopy());
                    Assert.assertFalse("Image must NOT have Bear subtype",
                            image.hasSubtype(SubType.BEAR, g));
                    Assert.assertTrue("Image must have no abilities under Humility",
                            image.getAbilities(g).isEmpty());
                });

        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Disenchant", "Humility");

        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Phantasmal Image", 0);
        assertGraveyardCount(playerA, "Phantasmal Image", 1);
        assertPermanentCount(playerB, "Humility", 0);
        assertPowerToughness(playerB, "Runeclaw Bear", 2, 2);
    }

    @Test
    public void testVesuvaHumilityFirst_CopyPreserved() {
        addCard(Zone.BATTLEFIELD, playerB, "Humility", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Glimmerpost", 1);

        addCard(Zone.HAND, playerA, "Vesuva", 1);

        playLand(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Vesuva");
        setChoice(playerA, true);
        setChoice(playerA, "Glimmerpost");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        // Vesuva is a land: Humility (creatures only) must not suppress its copy replacement.
        assertPermanentCount(playerA, "Glimmerpost", 1);
        assertPermanentCount(playerB, "Glimmerpost", 1);
    }

    @Test
    public void testCloneDressDownFirst_NoCopyDecision() {
        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Dress Down", 1);

        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.HAND, playerA, "Clone", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Clone");
        // No setChoice: generic creature ability remover must also suppress the self copy replacement.

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        // Clone enters as itself 0/0 (Dress Down sets no P/T) and dies to SBA; never a Bear copy.
        assertPermanentCount(playerA, "Clone", 0);
        assertGraveyardCount(playerA, "Clone", 1);
        assertPermanentCount(playerA, "Runeclaw Bear", 0);
    }
}
