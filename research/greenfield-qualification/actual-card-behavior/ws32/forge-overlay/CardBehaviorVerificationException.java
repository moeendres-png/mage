package forge.game;

/**
 * Sanitized production signal for an actual-card semantic assertion failure.
 * Expected/actual state is intentionally excluded from the exception payload.
 */
public final class CardBehaviorVerificationException extends RuntimeException {
    public static final String PUBLIC_MESSAGE = "card behavior verification failed";

    public CardBehaviorVerificationException() {
        super(PUBLIC_MESSAGE);
    }
}
