package forge.game;

/** Fail-closed carrier for a public WS20 failure outcome. */
public final class Ws20FailureException extends RuntimeException {
    private final Ws20FailureSignal outcome;

    public Ws20FailureException(final Ws20FailureSignal outcome) {
        super(outcome == null ? "WS20_FAILURE" : outcome.getCategory());
        if (outcome == null) {
            throw new IllegalArgumentException("outcome is required");
        }
        this.outcome = outcome;
    }

    public Ws20FailureSignal getOutcome() {
        return outcome;
    }
}