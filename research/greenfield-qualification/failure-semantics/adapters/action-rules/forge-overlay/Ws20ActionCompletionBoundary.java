package forge.gamemodes.match.input;

import forge.game.Game;
import forge.game.GameEntity;
import forge.game.Ws20FailureException;
import forge.game.Ws20FailureSignal;
import forge.game.card.Card;
import forge.game.player.Player;

/**
 * Revalidates the engine identity selected by an already accepted external
 * response immediately before the authoritative Input mutates selection state.
 */
public final class Ws20ActionCompletionBoundary {
    private Ws20ActionCompletionBoundary() { }

    public static <T extends GameEntity> void requireCompletable(final Game game,
                                                                 final ExternalDecisionResponse response,
                                                                 final Iterable<T> authoritativeOptions) {
        if (game == null || response == null || authoritativeOptions == null) {
            throw new IllegalArgumentException("authoritative action context is required");
        }
        if (response.isCancel()) {
            return;
        }

        for (final String selectedOptionId : response.getSelectedOptionIds()) {
            T selected = null;
            for (final T candidate : authoritativeOptions) {
                if (ExternalDecisionRequest.optionIdFor(candidate).equals(selectedOptionId)) {
                    selected = candidate;
                    break;
                }
            }
            if (selected == null || !isCurrentEngineEntity(game, selected)) {
                fail("forge-game:" + game.getId(), response.getDecisionId(), response.getPrincipalId());
            }
        }
    }

    private static boolean isCurrentEngineEntity(final Game game, final GameEntity selected) {
        if (selected instanceof Player player) {
            return player.isInGame();
        }
        if (selected instanceof Card card) {
            final Card current = game.getCardState(card);
            return current != null
                    && current.getGameTimestamp() == card.getGameTimestamp()
                    && game.getZoneOf(current) != null;
        }
        return false;
    }

    /** Fault-injection entrypoint exercising the exact throwing path used above. */
    public static void injectNotCompletableForContractTest(final String gameId,
                                                            final long decisionId,
                                                            final int principalId) {
        fail(gameId, decisionId, principalId);
    }

    private static void fail(final String gameId, final long decisionId, final int principalId) {
        throw new Ws20FailureException(
                Ws20FailureSignal.actionNotCompletable(gameId, decisionId, principalId));
    }
}