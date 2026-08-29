package forge.gamemodes.match.input;

/**
 * Technical request/response transport failure. The public exception message is
 * deliberately fixed; raw channel, serialization and payload details are not
 * exposed through the authoritative outcome envelope.
 */
public final class ExternalDecisionTransportException extends RuntimeException {
    public enum Stage {
        CONNECT,
        WRITE_REQUEST,
        READ_RESPONSE,
        DECODE_RESPONSE
    }

    private final Stage stage;
    private final long decisionId;
    private final int principalId;

    public ExternalDecisionTransportException(final Stage stage, final long decisionId, final int principalId) {
        super("decision transport failed");
        this.stage = stage;
        this.decisionId = decisionId;
        this.principalId = principalId;
    }

    public Stage getStage() { return stage; }
    public long getDecisionId() { return decisionId; }
    public int getPrincipalId() { return principalId; }
}
