package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.CardBehaviorVerificationException;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.input.UnifiedOutcome;
import forge.gamemodes.match.input.UnifiedOutcomeCategory;
import forge.gamemodes.match.input.UnifiedOutcomeMapper;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 * WS32 qualification-only actual-card runtime witness.
 *
 * The production hook is generic.  Card-specific expectations exist only in
 * this witness.  The scenario reuses the WS26 Mulldrifter ChangesZone ETB path:
 * real zone movement -> trigger collection -> authoritative stack ->
 * MagicStack.resolveStack -> post-resolution production verifier.
 */
public class Ws32CardBehaviorFailureQualificationTest extends AITest {
    private static final String FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928";

    private static final class Result {
        int handBefore;
        int libraryBefore;
        int actualHand;
        int actualLibrary;
        int expectedHand;
        int expectedLibrary;
        int hookCalls;
        boolean stackEmptyAtHook;
        boolean semanticMatch;
        boolean stagedStatePublished;
        UnifiedOutcome publicFailure;
    }

    private Result runScenario(final boolean controlledMismatch) {
        final Game game = initAndCreateGame();
        final Player player = game.getPlayers().get(0);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, player);

        final Card mulldrifter = addCardToZone("Mulldrifter", player, ZoneType.Hand);
        addCardToZone("Storm Crow", player, ZoneType.Library);
        addCardToZone("Sol Ring", player, ZoneType.Library);

        final Result result = new Result();
        result.handBefore = player.getCardsIn(ZoneType.Hand).size();
        result.libraryBefore = player.getCardsIn(ZoneType.Library).size();
        result.expectedHand = result.handBefore + 1 + (controlledMismatch ? 1 : 0);
        result.expectedLibrary = result.libraryBefore - 2;

        final int[] hookCalls = {0};
        final boolean[] stackEmpty = {false};
        final int[] actualHand = {-1};
        final int[] actualLibrary = {-1};
        final boolean[] stagedPublished = {false};

        game.setCardBehaviorVerifier((resolvedGame, resolvedAbility) -> {
            hookCalls[0]++;
            actualHand[0] = player.getCardsIn(ZoneType.Hand).size();
            actualLibrary[0] = player.getCardsIn(ZoneType.Library).size();
            stackEmpty[0] = resolvedGame.getStack().isEmpty();
            if (actualHand[0] != result.expectedHand || actualLibrary[0] != result.expectedLibrary) {
                throw new CardBehaviorVerificationException();
            }
            stagedPublished[0] = true;
        });

        game.getAction().moveTo(ZoneType.Battlefield, mulldrifter, null, null);
        Assert.assertTrue(mulldrifter.isInZone(ZoneType.Battlefield));
        Assert.assertTrue(game.getTriggerHandler().runWaitingTriggers(), "actual ChangesZone trigger must be collected");
        Assert.assertTrue(game.getStack().hasSimultaneousStackEntries());
        Assert.assertTrue(game.getStack().addAllTriggeredAbilitiesToStack());
        Assert.assertFalse(game.getStack().isEmpty());

        CardBehaviorVerificationException caught = null;
        try {
            game.getStack().resolveStack();
        } catch (CardBehaviorVerificationException ex) {
            caught = ex;
        }

        result.hookCalls = hookCalls[0];
        result.stackEmptyAtHook = stackEmpty[0];
        result.actualHand = actualHand[0];
        result.actualLibrary = actualLibrary[0];
        result.semanticMatch = result.actualHand == result.expectedHand
                && result.actualLibrary == result.expectedLibrary;
        result.stagedStatePublished = stagedPublished[0];

        Assert.assertEquals(result.hookCalls, 1, "production verifier hook must execute exactly once");
        Assert.assertTrue(result.stackEmptyAtHook, "hook must execute after finishResolving removed the resolved trigger");
        Assert.assertEquals(result.actualLibrary, result.libraryBefore - 2,
                "Rules Core must have completed the actual-card draw before verification");
        Assert.assertEquals(result.actualHand, result.handBefore + 1,
                "Rules Core must have completed the actual-card draw before verification");

        if (!controlledMismatch) {
            Assert.assertNull(caught);
            Assert.assertTrue(result.semanticMatch);
            Assert.assertTrue(result.stagedStatePublished,
                    "accepted semantic state may cross the simulator publication boundary");
            return result;
        }

        Assert.assertNotNull(caught, "controlled semantic mismatch must fail at production hook");
        Assert.assertFalse(result.semanticMatch);
        Assert.assertFalse(result.stagedStatePublished,
                "failed semantic state must not cross the simulator publication boundary");
        Assert.assertEquals(caught.getMessage(), CardBehaviorVerificationException.PUBLIC_MESSAGE);

        final UnifiedOutcomeCategory category = UnifiedOutcomeMapper.fromCardBehaviorFailure(caught);
        Assert.assertEquals(category, UnifiedOutcomeCategory.CARD_BEHAVIOR_FAILURE);
        result.publicFailure = UnifiedOutcome.failure(category,
                "ws32-controlled-semantic-mismatch", "ws32-isolated-game", null, player.getId());
        Assert.assertFalse(result.publicFailure.isStateCommitted());
        Assert.assertEquals(result.publicFailure.getPublicMessage(), "card behavior verification failed");
        return result;
    }

    @Test
    public void actualCardProductionVerifierBindsTypedFailureWithoutPublishingFailedState() throws Exception {
        final Result positive = runScenario(false);
        final Result mismatch = runScenario(true);

        Assert.assertNotNull(mismatch.publicFailure);
        Assert.assertNotEquals(mismatch.publicFailure.getCategory(), UnifiedOutcomeCategory.ENGINE_FAILURE,
                "semantic mismatch after successful engine resolution is not ENGINE_FAILURE");

        final String json = "{"
                + "\"schema\":\"commander-simulator-next.ws32-runtime-witness.v1\","
                + "\"forge_pin\":\"" + FORGE_PIN + "\","
                + "\"production_hook\":\"forge.game.zone.MagicStack#resolveStack:post-finishResolving\","
                + "\"actual_card_runtime_path\":\"Hand->Battlefield->ChangesZone trigger->regular stack->MagicStack.resolveStack->semantic verifier\","
                + "\"positive\":{"
                + "\"hook_calls\":" + positive.hookCalls + ","
                + "\"stack_empty_at_hook\":" + positive.stackEmptyAtHook + ","
                + "\"expected_hand\":" + positive.expectedHand + ","
                + "\"actual_hand\":" + positive.actualHand + ","
                + "\"expected_library\":" + positive.expectedLibrary + ","
                + "\"actual_library\":" + positive.actualLibrary + ","
                + "\"semantic_match\":" + positive.semanticMatch + ","
                + "\"staged_state_published\":" + positive.stagedStatePublished + "},"
                + "\"controlled_mismatch\":{"
                + "\"hook_calls\":" + mismatch.hookCalls + ","
                + "\"stack_empty_at_hook\":" + mismatch.stackEmptyAtHook + ","
                + "\"expected_hand\":" + mismatch.expectedHand + ","
                + "\"actual_hand\":" + mismatch.actualHand + ","
                + "\"expected_library\":" + mismatch.expectedLibrary + ","
                + "\"actual_library\":" + mismatch.actualLibrary + ","
                + "\"semantic_match\":" + mismatch.semanticMatch + ","
                + "\"engine_execution\":\"PASS_BEFORE_CONTROLLED_VERIFIER_FAILURE\","
                + "\"staged_state_published\":" + mismatch.stagedStatePublished + "},"
                + "\"public_failure\":{"
                + "\"schema\":\"" + UnifiedOutcome.SCHEMA + "\","
                + "\"category\":\"" + mismatch.publicFailure.getCategory().name() + "\","
                + "\"correlation_id\":\"" + mismatch.publicFailure.getCorrelationId() + "\","
                + "\"game_id\":\"" + mismatch.publicFailure.getGameId() + "\","
                + "\"decision_id\":null,"
                + "\"principal_id\":" + mismatch.publicFailure.getPrincipalId() + ","
                + "\"public_message\":\"" + mismatch.publicFailure.getPublicMessage() + "\","
                + "\"state_committed\":" + mismatch.publicFailure.isStateCommitted() + "},"
                + "\"fallback_used\":false,"
                + "\"stdout_only\":false}"
                + System.lineSeparator();

        final String configured = System.getProperty("ws32.out");
        Assert.assertNotNull(configured, "-Dws32.out is required for immutable evidence");
        final Path out = Path.of(configured);
        Files.createDirectories(out.getParent());
        Files.writeString(out, json, StandardCharsets.UTF_8);

        System.out.println("WS32_RUNTIME_HOOK_EXECUTED=TRUE");
        System.out.println("WS32_POSITIVE_CONTROL=PASS");
        System.out.println("WS32_CONTROLLED_SEMANTIC_MISMATCH=DETECTED");
        System.out.println("WS32_TYPED_OUTCOME=CARD_BEHAVIOR_FAILURE");
        System.out.println("WS32_STATE_COMMITTED=FALSE");
        System.out.println("WS32_FALLBACK_USED=FALSE");
    }
}
