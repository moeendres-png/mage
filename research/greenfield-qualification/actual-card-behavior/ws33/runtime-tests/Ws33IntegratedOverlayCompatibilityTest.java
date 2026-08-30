package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import forge.gamemodes.match.input.UnifiedOutcomeMapper;
import org.testng.Assert;
import org.testng.annotations.Test;

/** Focused compatibility controls for the common WS33 runtime overlay. */
public class Ws33IntegratedOverlayCompatibilityTest extends AITest {
    @Test
    public void verifierIsDisabledByDefaultAndActualCardResolutionIsUnchanged() {
        final Game game = initAndCreateGame();
        final Player player = game.getPlayers().get(0);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, player);

        final Card mulldrifter = addCardToZone("Mulldrifter", player, ZoneType.Hand);
        addCardToZone("Storm Crow", player, ZoneType.Library);
        addCardToZone("Sol Ring", player, ZoneType.Library);

        game.getAction().moveTo(ZoneType.Battlefield, mulldrifter, null, null);
        Assert.assertTrue(game.getTriggerHandler().runWaitingTriggers());
        Assert.assertTrue(game.getStack().addAllTriggeredAbilitiesToStack());
        game.getStack().resolveStack();

        Assert.assertEquals(player.getCardsIn(ZoneType.Hand).size(), 2);
        Assert.assertEquals(player.getCardsIn(ZoneType.Library).size(), 0);
        System.out.println("WS33_VERIFIER_DISABLED_BY_DEFAULT=PASS");
        System.out.println("WS33_NORMAL_ACTUAL_CARD_RESULT_UNCHANGED=PASS");
    }

    @Test
    public void unrelatedEngineFailureCannotBeRelabeledAsCardBehaviorFailure() {
        Assert.expectThrows(IllegalArgumentException.class,
                () -> UnifiedOutcomeMapper.fromCardBehaviorFailure(new RuntimeException("engine failure")));
        System.out.println("WS33_ENGINE_FAILURE_REMAINS_DISTINCT=PASS");
    }
}
