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
 * WS27 qualification-only actual-card witness.
 *
 * Exercises the exact Swiftwater Cliffs script through Forge zone movement,
 * replacement handling, trigger collection, stack ordering, and normal
 * resolution. No effect is directly constructed or resolved and no pilot
 * choice is required by the claimed GainLife V2 path.
 */
public final class Ws27SwiftwaterCliffsWitnessTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";
    private static final String ORACLE_ID = "2f4ad084-2062-44c0-9975-15f100204531";
    private static final String PATH_ID = "forge-behavior-v2:ede58d662fddba65852ba12b8bb699c33eb8e708";

    @Test
    public void actualCardGainLifePathRetainsSemanticState() throws Exception {
        final Game game = initAndCreateGame();
        final Player player = game.getPlayers().get(0);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, player);

        final Card cliffs = addCardToZone("Swiftwater Cliffs", player, ZoneType.Hand);
        final int lifeBefore = player.getLife();
        final int handBefore = player.getCardsIn(ZoneType.Hand).size();

        Assert.assertTrue(cliffs.isInZone(ZoneType.Hand), "actual corpus card must begin in hand");

        game.getAction().moveTo(ZoneType.Battlefield, cliffs, null, null);

        final int lifeAfterMove = player.getLife();
        final int handAfterMove = player.getCardsIn(ZoneType.Hand).size();
        Assert.assertTrue(cliffs.isInZone(ZoneType.Battlefield), "actual corpus land must enter battlefield");
        Assert.assertTrue(cliffs.isTapped(), "actual Swiftwater Cliffs replacement must make it enter tapped");
        Assert.assertEquals(handAfterMove, handBefore - 1, "zone movement must remove the land from hand");
        Assert.assertEquals(lifeAfterMove, lifeBefore, "life trigger must not resolve during zone movement");
        Assert.assertTrue(game.getStack().isEmpty(), "regular stack must be empty before waiting triggers transfer");

        Assert.assertTrue(game.getTriggerHandler().runWaitingTriggers(),
                "actual ChangesZone trigger must be collected");
        Assert.assertTrue(game.getStack().hasSimultaneousStackEntries(),
                "trigger must await authoritative simultaneous-stack transfer");
        Assert.assertTrue(game.getStack().addAllTriggeredAbilitiesToStack(),
                "trigger must transfer to the regular stack");
        Assert.assertFalse(game.getStack().isEmpty(), "trigger must be on the regular stack before resolution");

        playUntilStackClear(game);

        final int lifeFinal = player.getLife();
        Assert.assertEquals(lifeFinal, lifeBefore + 1,
                "actual GainLife effect must increase life by exactly one");
        Assert.assertTrue(cliffs.isInZone(ZoneType.Battlefield), "land must remain on battlefield");
        Assert.assertTrue(cliffs.isTapped(), "land must remain tapped after ETB resolution");
        Assert.assertTrue(game.getStack().isEmpty(), "resolution must empty the regular stack");
        Assert.assertFalse(game.getStack().hasSimultaneousStackEntries(),
                "no simultaneous trigger may remain after resolution");

        final String trace = "{"
                + "\"schema\":\"commander-simulator-next.ws27.engine-state-trace.v1\","
                + "\"forge_pin\":\"" + FORGE_PIN + "\","
                + "\"v2_path_id\":\"" + PATH_ID + "\","
                + "\"oracle_identity\":\"" + ORACLE_ID + "\","
                + "\"scenario\":\"Swiftwater Cliffs actual-card ETB GainLife through Rules Core\","
                + "\"initial\":{\"zone\":\"Hand\",\"life\":" + lifeBefore + ",\"hand_size\":" + handBefore + "},"
                + "\"after_move\":{\"zone\":\"Battlefield\",\"life\":" + lifeAfterMove
                + ",\"hand_size\":" + handAfterMove + ",\"tapped\":" + cliffs.isTapped()
                + ",\"regular_stack_empty\":true},"
                + "\"final\":{\"zone\":\"Battlefield\",\"life\":" + lifeFinal
                + ",\"tapped\":" + cliffs.isTapped()
                + ",\"stack_empty\":true,\"simultaneous_stack_entries\":false},"
                + "\"actual_card_execution\":true,"
                + "\"actual_rules_core_path\":true,"
                + "\"silent_fallbacks\":0,"
                + "\"stdout_only\":false"
                + "}"
                + System.lineSeparator();

        final String outputArg = System.getProperty("ws27.traceOut",
                "target/ws27-runtime/ws27-swiftwater-cliffs.trace.json");
        final Path out = Path.of(outputArg);
        Files.createDirectories(out.getParent());
        Files.writeString(out, trace, StandardCharsets.UTF_8);
    }
}
