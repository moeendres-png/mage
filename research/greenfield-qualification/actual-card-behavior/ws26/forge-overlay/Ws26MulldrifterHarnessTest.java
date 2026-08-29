package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/** Qualification-only WS26 harness fixture. Uses the pinned Mulldrifter card script
 * through Forge's real zone movement, trigger collection, stack ordering and
 * resolution path. It does not construct an effect definition or call resolve()
 * directly. */
public class Ws26MulldrifterHarnessTest extends AITest {
    @Test
    public void corpusCardEtbTriggerUsesRulesCoreAndRetainsSemanticState() throws Exception {
        final Game game = initAndCreateGame();
        final Player player = game.getPlayers().get(0);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, player);

        final Card mulldrifter = addCardToZone("Mulldrifter", player, ZoneType.Hand);
        addCardToZone("Storm Crow", player, ZoneType.Library);
        addCardToZone("Sol Ring", player, ZoneType.Library);

        final int lifeBefore = player.getLife();
        final int handBefore = player.getCardsIn(ZoneType.Hand).size();
        final int libraryBefore = player.getCardsIn(ZoneType.Library).size();
        Assert.assertTrue(handBefore >= 1, "Mulldrifter must be in hand");
        Assert.assertTrue(libraryBefore >= 2, "fixture needs two actual cards in library");

        game.getAction().moveTo(ZoneType.Battlefield, mulldrifter, null, null);
        Assert.assertTrue(mulldrifter.isInZone(ZoneType.Battlefield), "actual corpus card must enter battlefield");
        final int handAfterMove = player.getCardsIn(ZoneType.Hand).size();
        Assert.assertEquals(handAfterMove, handBefore - 1, "zone movement must precede ETB trigger resolution");
        Assert.assertTrue(game.getStack().isEmpty(), "trigger must not resolve during movement");

        Assert.assertTrue(game.getTriggerHandler().runWaitingTriggers(), "actual ChangesZone trigger must be collected");
        Assert.assertTrue(game.getStack().hasSimultaneousStackEntries(), "trigger must await authoritative stack ordering");
        Assert.assertTrue(game.getStack().addAllTriggeredAbilitiesToStack(), "trigger must transfer to regular stack");
        Assert.assertFalse(game.getStack().isEmpty(), "trigger must be on regular stack before resolution");

        playUntilStackClear(game);

        final int handFinal = player.getCardsIn(ZoneType.Hand).size();
        final int libraryFinal = player.getCardsIn(ZoneType.Library).size();
        Assert.assertEquals(handFinal, handBefore + 1, "Mulldrifter ETB must draw exactly two cards after leaving hand");
        Assert.assertEquals(libraryFinal, libraryBefore - 2, "exactly two cards must leave library");
        Assert.assertEquals(player.getLife(), lifeBefore, "fixture does not modify life");
        Assert.assertTrue(game.getStack().isEmpty(), "resolution must empty the stack");
        Assert.assertFalse(game.getStack().hasSimultaneousStackEntries(), "no pending simultaneous trigger may remain");

        final String trace = "{"
                + "\"schema\":\"commander-simulator-next.ws26.engine-state-trace.v1\","
                + "\"forge_pin\":\"8c7e9afb8e6caee88644b94e25da5852e36f8928\","
                + "\"scenario\":\"Mulldrifter actual-card ChangesZone ETB through Rules Core\","
                + "\"oracle_id\":\"24d0f5e7-0d9e-4b76-900e-a7274e80312d\","
                + "\"initial\":{\"zone\":\"Hand\",\"hand_size\":" + handBefore + ",\"library_size\":" + libraryBefore + ",\"life\":" + lifeBefore + "},"
                + "\"after_move\":{\"zone\":\"Battlefield\",\"hand_size\":" + handAfterMove + ",\"regular_stack_empty\":true},"
                + "\"final\":{\"zone\":\"Battlefield\",\"hand_size\":" + handFinal + ",\"library_size\":" + libraryFinal + ",\"life\":" + player.getLife() + ",\"stack_empty\":true,\"simultaneous_stack_entries\":false},"
                + "\"stdout_only\":false}"
                + System.lineSeparator();
        final Path out = Path.of("target", "ws26-runtime", "ws26-mulldrifter.trace.json");
        Files.createDirectories(out.getParent());
        Files.writeString(out, trace, StandardCharsets.UTF_8);
    }
}
