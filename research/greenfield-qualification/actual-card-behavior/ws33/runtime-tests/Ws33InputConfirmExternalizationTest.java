package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.card.CardView;
import forge.game.player.Player;
import forge.gamemodes.match.input.ExternalDecisionRequest;
import forge.gamemodes.match.input.ExternalDecisionResponse;
import forge.gamemodes.match.input.ExternalDecisionTape;
import forge.gamemodes.match.input.ExternalDecisionValidationException;
import forge.gamemodes.match.input.InputConfirm;
import forge.player.LobbyPlayerHuman;
import forge.player.PlayerControllerHuman;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.util.List;
import java.util.concurrent.atomic.AtomicReference;

/** Focused generic INPUT_CONFIRM boundary test; no card identity is consulted. */
public class Ws33InputConfirmExternalizationTest extends AITest {
    @Test
    public void inputConfirmUsesAuthoritativeTypedOptionsAndRecordsOneAcceptedEvent() {
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final PlayerControllerHuman controller = new PlayerControllerHuman(
                game, actor, new LobbyPlayerHuman("ws33-external-principal"));
        final AtomicReference<ExternalDecisionRequest> captured = new AtomicReference<>();
        controller.setExternalDecisionProvider(request -> {
            captured.set(request);
            return new ExternalDecisionResponse(request.getDecisionId(), request.getToken(),
                    request.getActorId(), request.getPrincipalId(), request.getResponseSchema(),
                    List.of("choice:0"), false);
        });

        final boolean result = InputConfirm.confirm(controller, (CardView) null,
                "qualification-only prompt", false, List.of("affirm", "decline"));
        Assert.assertTrue(result);
        final ExternalDecisionRequest request = captured.get();
        Assert.assertNotNull(request);
        Assert.assertEquals(request.getDecisionKind(), "INPUT_CONFIRM");
        Assert.assertEquals(request.getMinimumSelection(), 1);
        Assert.assertEquals(request.getMaximumSelection(), 1);
        Assert.assertFalse(request.isCancelAllowed());
        Assert.assertEquals(request.getOptions().stream().map(ExternalDecisionRequest.Option::getOptionId).toList(),
                List.of("choice:0", "choice:1"));
        final List<ExternalDecisionTape.Event> tape = controller.getExternalDecisionTapeSnapshot();
        Assert.assertEquals(tape.size(), 1);
        Assert.assertEquals(tape.get(0).getDecisionKind(), "INPUT_CONFIRM");
        Assert.assertEquals(tape.get(0).getResponseStatus(), ExternalDecisionTape.ResponseStatus.ACCEPTED);
        Assert.assertEquals(tape.get(0).getSelectedOptionIds(), List.of("choice:0"));
        System.out.println("WS33_INPUT_CONFIRM_TYPED_ADAPTER=PASS");
    }

    @Test
    public void ambiguousConfirmationOptionsFailClosedBeforeProviderInvocation() {
        final Game game = initAndCreateGame();
        final Player actor = game.getPlayers().get(0);
        final PlayerControllerHuman controller = new PlayerControllerHuman(
                game, actor, new LobbyPlayerHuman("ws33-external-principal"));
        controller.setExternalDecisionProvider(request -> {
            throw new AssertionError("provider must not receive an ambiguous authoritative option set");
        });
        final ExternalDecisionValidationException error = Assert.expectThrows(
                ExternalDecisionValidationException.class,
                () -> InputConfirm.confirm(controller, (CardView) null,
                        "qualification-only prompt", false, List.of("same", "same")));
        Assert.assertEquals(error.getCode(),
                ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH);
        Assert.assertTrue(controller.getExternalDecisionTapeSnapshot().isEmpty());
        System.out.println("WS33_INPUT_CONFIRM_UNSUPPORTED_FORM_FAIL_CLOSED=PASS");
    }
}
