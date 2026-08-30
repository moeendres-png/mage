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

/**
 * Re-executes the rejected WS27 LifeGain path on the integrated WS33 overlay.
 * This is qualification-only code. The asserted behavior comes from the actual
 * card script and Forge lifecycle; no effect is directly constructed or resolved.
 */
public final class Ws33SwiftwaterCliffsWitnessTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final String ORACLE_ID = "2f4ad084-2062-44c0-9975-15f100204531";
    private static final String PATH_ID = "forge-behavior-v2:ede58d662fddba65852ba12b8bb699c33eb8e708";

    @Test
    public void actualCardGainLifePathProducesV21StateEvidence() throws Exception {
        final Game game = initAndCreateGame();
        final Player player = game.getPlayers().get(0);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, player);

        final Card cliffs = addCardToZone("Swiftwater Cliffs", player, ZoneType.Hand);
        final int lifeBefore = player.getLife();
        final int handBefore = player.getCardsIn(ZoneType.Hand).size();
        Assert.assertTrue(cliffs.isInZone(ZoneType.Hand));

        game.getAction().moveTo(ZoneType.Battlefield, cliffs, null, null);
        final int lifeAfterMove = player.getLife();
        final int handAfterMove = player.getCardsIn(ZoneType.Hand).size();
        Assert.assertTrue(cliffs.isInZone(ZoneType.Battlefield));
        Assert.assertTrue(cliffs.isTapped());
        Assert.assertEquals(handAfterMove, handBefore - 1);
        Assert.assertEquals(lifeAfterMove, lifeBefore);
        Assert.assertTrue(game.getStack().isEmpty());

        Assert.assertTrue(game.getTriggerHandler().runWaitingTriggers());
        Assert.assertTrue(game.getStack().hasSimultaneousStackEntries());
        Assert.assertTrue(game.getStack().addAllTriggeredAbilitiesToStack());
        Assert.assertFalse(game.getStack().isEmpty());
        playUntilStackClear(game);

        final int lifeFinal = player.getLife();
        Assert.assertEquals(lifeFinal, lifeBefore + 1);
        Assert.assertTrue(cliffs.isInZone(ZoneType.Battlefield));
        Assert.assertTrue(cliffs.isTapped());
        Assert.assertTrue(game.getStack().isEmpty());
        Assert.assertFalse(game.getStack().hasSimultaneousStackEntries());

        final String trace = "{"
                + "\"schema\":\"commander-simulator-next.ws33.engine-state-trace.v1\","
                + "\"forge_pin\":\"" + FORGE_PIN + "\","
                + "\"v2_path_id\":\"" + PATH_ID + "\","
                + "\"oracle_identity\":\"" + ORACLE_ID + "\","
                + "\"scenario_id\":\"ws33-lifegain-swiftwater-cliffs\","
                + "\"initial\":{\"zone\":\"Hand\",\"life\":" + lifeBefore + ",\"hand_size\":" + handBefore + "},"
                + "\"after_move\":{\"zone\":\"Battlefield\",\"life\":" + lifeAfterMove
                + ",\"hand_size\":" + handAfterMove + ",\"tapped\":" + cliffs.isTapped()
                + ",\"regular_stack_empty\":true,\"simultaneous_stack_entries\":true},"
                + "\"after_stack_transfer\":{\"regular_stack_nonempty\":true},"
                + "\"final\":{\"zone\":\"Battlefield\",\"life\":" + lifeFinal
                + ",\"tapped\":" + cliffs.isTapped()
                + ",\"stack_empty\":true,\"simultaneous_stack_entries\":false},"
                + "\"trace_event_ids\":[\"initial\",\"after_move\",\"after_stack_transfer\",\"final\"],"
                + "\"actual_card_execution\":true,\"actual_rules_core_path\":true,"
                + "\"authoritative_decision_boundary\":\"NOT_REQUIRED\","
                + "\"silent_fallbacks\":0,\"stdout_only\":false}"
                + System.lineSeparator();
        final Path out = Path.of(System.getProperty("ws33.swiftwaterTraceOut",
                "target/ws33-runtime/ws33-swiftwater-cliffs.trace.json"));
        Files.createDirectories(out.getParent());
        Files.writeString(out, trace, StandardCharsets.UTF_8);
    }
}
