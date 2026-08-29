package forge.game;

/**
 * Minimal public failure payload for the two WS20 actual-path bindings.
 *
 * <p>The shape intentionally mirrors commander-simulator-next.failure-outcome.v1
 * without carrying arbitrary exception text, card names, prompts, zones, or
 * other hidden-information-bearing values.</p>
 */
public final class Ws20FailureSignal {
    public static final String SCHEMA = "commander-simulator-next.failure-outcome.v1";
    public static final String ACTION_NOT_COMPLETABLE = "ACTION_NOT_COMPLETABLE";
    public static final String UNSUPPORTED_RULES_PATH = "UNSUPPORTED_RULES_PATH";

    private final String category;
    private final String correlationId;
    private final String gameId;
    private final Long decisionId;
    private final Integer principalId;
    private final String publicMessage;

    private Ws20FailureSignal(final String category, final String correlationId,
                              final String gameId, final Long decisionId,
                              final Integer principalId, final String publicMessage) {
        if (category == null || correlationId == null || correlationId.isEmpty()
                || gameId == null || gameId.isEmpty() || publicMessage == null || publicMessage.isEmpty()) {
            throw new IllegalArgumentException("public failure signal fields are required");
        }
        if (principalId == null || principalId < 0) {
            throw new IllegalArgumentException("principal id must be non-negative");
        }
        if (decisionId != null && decisionId < 1L) {
            throw new IllegalArgumentException("decision id must be positive when present");
        }
        this.category = category;
        this.correlationId = correlationId;
        this.gameId = gameId;
        this.decisionId = decisionId;
        this.principalId = principalId;
        this.publicMessage = publicMessage;
    }

    public static Ws20FailureSignal actionNotCompletable(final String gameId,
                                                          final long decisionId,
                                                          final int principalId) {
        return new Ws20FailureSignal(ACTION_NOT_COMPLETABLE,
                "ws20-action-" + gameId + "-" + decisionId,
                gameId, decisionId, principalId, "action is not completable");
    }

    public static Ws20FailureSignal unsupportedRulesPath(final String gameId,
                                                          final int principalId) {
        return new Ws20FailureSignal(UNSUPPORTED_RULES_PATH,
                "ws20-rules-" + gameId + "-" + principalId,
                gameId, null, principalId, "rules path is unsupported");
    }

    public String getSchema() { return SCHEMA; }
    public String getCategory() { return category; }
    public String getCorrelationId() { return correlationId; }
    public String getGameId() { return gameId; }
    public Long getDecisionId() { return decisionId; }
    public Integer getPrincipalId() { return principalId; }
    public String getPublicMessage() { return publicMessage; }
    public boolean isStateCommitted() { return false; }

    public String toPublicJson() {
        return "{"
                + "\"schema\":\"" + escape(SCHEMA) + "\","
                + "\"category\":\"" + escape(category) + "\","
                + "\"correlation_id\":\"" + escape(correlationId) + "\","
                + "\"game_id\":\"" + escape(gameId) + "\","
                + "\"decision_id\":" + (decisionId == null ? "null" : decisionId) + ","
                + "\"principal_id\":" + principalId + ","
                + "\"public_message\":\"" + escape(publicMessage) + "\","
                + "\"state_committed\":false"
                + "}";
    }

    private static String escape(final String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"");
    }
}