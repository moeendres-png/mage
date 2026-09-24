package org.mage.test.serverside.rg07;

import mage.abilities.ActivatedAbility;
import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.Game;
import mage.players.Player;
import mage.target.TargetPermanent;
import mage.filter.StaticFilters;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * RG-07 systemic regressions for authoritative legal-action offering.
 */
public class RG07TargetOfferingRegressionTest extends CardTestPlayerBase {

    private static final String HEX = "Hex";
    private static final String[] SIX_CREATURES = {
            "Grizzly Bears",
            "Silvercoat Lion",
            "Runeclaw Bear",
            "Hill Giant",
            "Walking Corpse",
            "Centaur Courser"
    };

    private static boolean isSpellOffered(Game game, Player player, String cardName) {
        for (ActivatedAbility ability : player.getPlayable(game, false)) {
            Card source = game.getCard(ability.getSourceId());
            if (source != null && cardName.equals(source.getName())) {
                return true;
            }
        }
        return false;
    }

    private void addSixDistinctCreatures() {
        for (String creature : SIX_CREATURES) {
            addCard(Zone.BATTLEFIELD, playerB, creature, 1);
        }
    }

    private static String sixCreatureTargets() {
        return String.join("^", SIX_CREATURES);
    }

    @Test
    public void hexRealCastSelectsExactlySixAndResolves() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        addSixDistinctCreatures();

        runCode("Hex is offered before real cast", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> Assert.assertTrue(isSpellOffered(game, player, HEX)));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, HEX, sixCreatureTargets(), true);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        for (String creature : SIX_CREATURES) {
            assertPermanentCount(playerB, creature, 0);
        }
        assertGraveyardCount(playerB, 6);
    }

    @Test
    public void hexproofReducesTargetPoolBelowExactMinimum() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Walking Corpse", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Centaur Courser", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Gladecover Scout", 1);

        runCode("Hex has only five legal targets", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> Assert.assertFalse(
                        "Hexproof creature must not count toward the six legal targets",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void offeringIsRecomputedWhenPreviouslyLegalTargetDisappears() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.HAND, playerA, "Shock", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 7);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 1);
        addSixDistinctCreatures();

        runCode("Hex initially offered", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> Assert.assertTrue(isSpellOffered(game, player, HEX)));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Shock", "Walking Corpse", true);

        runCode("Hex no longer offered after target leaves", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> Assert.assertFalse(
                        "Legal-action enumeration must re-evaluate target cardinality",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
        assertGraveyardCount(playerB, "Walking Corpse", 1);
    }

    @Test
    public void costReductionKeepsOfferingAndRealCastInAgreement() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Jet Medallion", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 5);
        addSixDistinctCreatures();

        runCode("Reduced Hex is offered with five mana", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> Assert.assertTrue(
                        "Cost-reduced getPlayable result must agree with cast legality",
                        isSpellOffered(game, player, HEX)));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, HEX, sixCreatureTargets(), true);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        for (String creature : SIX_CREATURES) {
            assertPermanentCount(playerB, creature, 0);
        }
    }

    @Test
    public void genericExactAndUpToCardinalitySemantics() {
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", 1);

        runCode("generic target cardinality", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            TargetPermanent exactTwo = new TargetPermanent(2, 2, StaticFilters.FILTER_PERMANENT_CREATURES);
            TargetPermanent upToTwo = new TargetPermanent(0, 2, StaticFilters.FILTER_PERMANENT_CREATURES);
            TargetPermanent zeroOnly = new TargetPermanent(0, 0, StaticFilters.FILTER_PERMANENT_CREATURES);

            Assert.assertFalse("Exact two must reject a one-object target pool",
                    exactTwo.canChooseFromPossibleTargets(player.getId(), null, game));
            Assert.assertTrue("Up-to-two must remain legal with one available target",
                    upToTwo.canChooseFromPossibleTargets(player.getId(), null, game));
            Assert.assertTrue("Zero-target semantics must be legal without selecting an object",
                    zeroOnly.canChooseFromPossibleTargets(player.getId(), null, game));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
