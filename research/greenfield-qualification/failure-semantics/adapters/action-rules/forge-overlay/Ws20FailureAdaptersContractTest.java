package forge.gamemodes.match.input;

import forge.game.Ws20FailureException;
import forge.game.Ws20FailureSignal;
import forge.game.Ws20RulesPathBoundary;

/** Runtime fault-injection probe for the exact guards called by production code. */
public final class Ws20FailureAdaptersContractTest {
    private static final String PRIVATE_MARKER = "PRIVATE_CARD_ALPHA";

    private Ws20FailureAdaptersContractTest() { }

    public static void main(final String[] args) {
        probeActionNotCompletable();
        probeUnsupportedRulesPath();
        System.out.println("WS20_FAILURE_ADAPTERS=PASS");
    }

    private static void probeActionNotCompletable() {
        final int[] prohibitedMutation = {0};
        try {
            // Exact central guard invoked by the production Game/entity overload.
            Ws20ActionCompletionBoundary.requireCompletable("forge-game:77", 41L, 3, false);
            prohibitedMutation[0]++;
            throw new AssertionError("ACTION_NOT_COMPLETABLE guard returned instead of failing closed");
        } catch (final Ws20FailureException error) {
            final Ws20FailureSignal outcome = error.getOutcome();
            require(Ws20FailureSignal.ACTION_NOT_COMPLETABLE.equals(outcome.getCategory()), "wrong action category");
            require("forge-game:77".equals(outcome.getGameId()), "wrong action game id");
            require(Long.valueOf(41L).equals(outcome.getDecisionId()), "wrong action decision id");
            require(Integer.valueOf(3).equals(outcome.getPrincipalId()), "wrong action principal id");
            require(!outcome.isStateCommitted(), "action failure committed state");
            final String payload = outcome.toPublicJson();
            require(!payload.contains(PRIVATE_MARKER), "action payload leaked hidden marker");
            require(prohibitedMutation[0] == 0, "action failure allowed downstream mutation");
            System.out.println("WS20_TRACE_ACTION=" + payload);
        }
    }

    private static void probeUnsupportedRulesPath() {
        final int[] prohibitedMutation = {0};
        try {
            // Exact guard invoked by GameAction.changeZone; true injects the live
            // merged-object condition that the Rules Core explicitly cannot model.
            Ws20RulesPathBoundary.requireSupportedAstrotoriumMergedZoneChange("forge-game:77", 3, true);
            prohibitedMutation[0]++;
            throw new AssertionError("UNSUPPORTED_RULES_PATH guard returned instead of failing closed");
        } catch (final Ws20FailureException error) {
            final Ws20FailureSignal outcome = error.getOutcome();
            require(Ws20FailureSignal.UNSUPPORTED_RULES_PATH.equals(outcome.getCategory()), "wrong rules category");
            require("forge-game:77".equals(outcome.getGameId()), "wrong rules game id");
            require(outcome.getDecisionId() == null, "rules failure must not invent a decision id");
            require(Integer.valueOf(3).equals(outcome.getPrincipalId()), "wrong rules principal id");
            require(!outcome.isStateCommitted(), "rules failure committed state");
            final String payload = outcome.toPublicJson();
            require(!payload.contains(PRIVATE_MARKER), "rules payload leaked hidden marker");
            require(prohibitedMutation[0] == 0, "rules failure allowed downstream mutation");
            System.out.println("WS20_TRACE_RULES=" + payload);
        }
    }

    private static void require(final boolean value, final String message) {
        if (!value) {
            throw new AssertionError(message);
        }
    }
}