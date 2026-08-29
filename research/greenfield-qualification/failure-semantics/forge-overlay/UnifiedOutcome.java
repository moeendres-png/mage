package forge.gamemodes.match.input;

/**
 * Public, principal-scoped outcome envelope. Arbitrary exception messages are
 * deliberately excluded so a technical failure cannot become a hidden-data
 * side channel.
 */
public final class UnifiedOutcome {
    public static final String SCHEMA = "commander-simulator-next.failure-outcome.v1";

    private final UnifiedOutcomeCategory category;
    private final String correlationId;
    private final String gameId;
    private final Long decisionId;
    private final Integer principalId;
    private final boolean stateCommitted;

    private UnifiedOutcome(final UnifiedOutcomeCategory category, final String correlationId,
                           final String gameId, final Long decisionId, final Integer principalId,
                           final boolean stateCommitted) {
        if (category == null || correlationId == null || correlationId.isEmpty()
                || gameId == null || gameId.isEmpty()) {
            throw new IllegalArgumentException("typed outcome fields are required");
        }
        if (stateCommitted != category.isCommitRequired()) {
            throw new IllegalArgumentException("outcome violates authoritative commit policy");
        }
        this.category = category;
        this.correlationId = correlationId;
        this.gameId = gameId;
        this.decisionId = decisionId;
        this.principalId = principalId;
        this.stateCommitted = stateCommitted;
    }

    public static UnifiedOutcome success(final String correlationId, final String gameId,
                                         final Long decisionId, final Integer principalId) {
        return new UnifiedOutcome(UnifiedOutcomeCategory.SUCCESS, correlationId, gameId,
                decisionId, principalId, true);
    }

    public static UnifiedOutcome failure(final UnifiedOutcomeCategory category,
                                         final String correlationId, final String gameId,
                                         final Long decisionId, final Integer principalId) {
        if (category == UnifiedOutcomeCategory.SUCCESS) {
            throw new IllegalArgumentException("SUCCESS must use the committed success constructor");
        }
        return new UnifiedOutcome(category, correlationId, gameId, decisionId, principalId, false);
    }

    public UnifiedOutcomeCategory getCategory() { return category; }
    public String getCorrelationId() { return correlationId; }
    public String getGameId() { return gameId; }
    public Long getDecisionId() { return decisionId; }
    public Integer getPrincipalId() { return principalId; }
    public String getPublicMessage() { return category.getPublicMessage(); }
    public boolean isStateCommitted() { return stateCommitted; }
}
