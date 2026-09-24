package org.mage.test.serverside.rg07;

import mage.abilities.Ability;
import mage.abilities.ActivatedAbility;
import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.Game;
import mage.filter.StaticFilters;
import mage.players.Player;
import mage.target.TargetPermanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * RG-07 baseline reproducer for exact-N target legal-action offering.
 */
public class RG07HexPlayableBaselineTest extends CardTestPlayerBase {

    private static final String HEX = "Hex";

    private static boolean isSpellOffered(Game game, Player player, String cardName) {
        for (ActivatedAbility ability : player.getPlayable(game, false)) {
            Card source = game.getCard(ability.getSourceId());
            if (source != null && cardName.equals(source.getName())) {
                return true;
            }
        }
        return false;
    }

    private void configureHexWithCreatureCount(int creatures) {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", creatures);
    }

    @Test
    public void hexNotOfferedWithFiveLegalCreatures() {
        configureHexWithCreatureCount(5);

        runCode("Hex offer with five targets", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                Assert.assertFalse("Hex must not be offered with only five legal creature targets",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void hexOfferedWithExactlySixLegalCreatures() {
        configureHexWithCreatureCount(6);

        runCode("Hex offer with six targets", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                Assert.assertTrue("Hex must be offered with exactly six legal creature targets",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void hexOfferedWithSevenLegalCreatures() {
        configureHexWithCreatureCount(7);

        runCode("Hex offer with seven targets", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                Assert.assertTrue("Hex must be offered when more than six legal creature targets exist",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
    private static final String SIX_TARGETS =
            "Grizzly Bears^Silvercoat Lion^Walking Corpse^Runeclaw Bear^Wind Drake^Hill Giant";

    private void configureSixDistinctCreatures() {
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Walking Corpse", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Wind Drake", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Hill Giant", 1);
    }

    @Test
    public void hexActualCastSelectsExactlySixTargets() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        configureSixDistinctCreatures();

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, HEX, SIX_TARGETS);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertGraveyardCount(playerB, "Silvercoat Lion", 1);
        assertGraveyardCount(playerB, "Walking Corpse", 1);
        assertGraveyardCount(playerB, "Runeclaw Bear", 1);
        assertGraveyardCount(playerB, "Wind Drake", 1);
        assertGraveyardCount(playerB, "Hill Giant", 1);
    }

    @Test
    public void hexWithSevenTargetsCastsWithExactlySixAndLeavesSeventh() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        configureSixDistinctCreatures();
        addCard(Zone.BATTLEFIELD, playerB, "Centaur Courser", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, HEX, SIX_TARGETS);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertPermanentCount(playerB, "Centaur Courser", 1);
        assertPermanentCount(playerB, 1);
    }

    @Test
    public void hexproofReducesLegalPoolBelowSixSoHexIsNotOffered() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Walking Corpse", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Runeclaw Bear", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Wind Drake", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Slippery Bogle", 1);

        runCode("Hex offer respects hexproof-reduced pool", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> Assert.assertFalse(
                        "Opponent hexproof creature must not satisfy Hex's six legal targets",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void oneTargetBecomingIllegalAfterOfferingDoesNotCorruptResolution() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        configureSixDistinctCreatures();

        addCard(Zone.HAND, playerB, "Unsummon", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Island", 1);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, HEX, SIX_TARGETS);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerB, "Unsummon", "Grizzly Bears", HEX);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertHandCount(playerB, "Grizzly Bears", 1);
        assertGraveyardCount(playerB, "Silvercoat Lion", 1);
        assertGraveyardCount(playerB, "Walking Corpse", 1);
        assertGraveyardCount(playerB, "Runeclaw Bear", 1);
        assertGraveyardCount(playerB, "Wind Drake", 1);
        assertGraveyardCount(playerB, "Hill Giant", 1);
    }

    @Test
    public void costReductionGetPlayableAgreesWithActualHexCast() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 5);
        addCard(Zone.BATTLEFIELD, playerA, "Jet Medallion", 1);
        configureSixDistinctCreatures();

        runCode("Reduced Hex is offered", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> Assert.assertTrue(
                        "Jet Medallion reduction must be reflected by getPlayable",
                        isSpellOffered(game, player, HEX)));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, HEX, SIX_TARGETS);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertPermanentCount(playerB, 0);
    }

    @Test
    public void genericTargetCardinalitySemanticsRemainConsistent() {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", 1);

        runCode("Generic target cardinality", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Card hex = player.getHand().getCards(game).stream()
                    .filter(card -> HEX.equals(card.getName()))
                    .findFirst()
                    .orElseThrow(() -> new AssertionError("Hex must be in hand"));
            Ability source = hex.getSpellAbility();

            TargetPermanent exactTwo = new TargetPermanent(2, StaticFilters.FILTER_PERMANENT_CREATURES);
            Assert.assertFalse("one creature cannot satisfy exact-two targeting",
                    exactTwo.canChooseFromPossibleTargets(player.getId(), source, game));

            TargetPermanent upToTwo = new TargetPermanent(0, 2, StaticFilters.FILTER_PERMANENT_CREATURES);
            Assert.assertTrue("up-to-two targeting must remain legal with zero or one selection",
                    upToTwo.canChooseFromPossibleTargets(player.getId(), source, game));

            TargetPermanent optionalZero = new TargetPermanent(0, 0, StaticFilters.FILTER_PERMANENT_CREATURES);
            Assert.assertTrue("zero-target choice must be legal when min=max=0",
                    optionalZero.canChooseFromPossibleTargets(player.getId(), source, game));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }


}
