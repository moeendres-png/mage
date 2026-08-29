package forge.gamemodes.match.input;

/** Exhaustive translation from the existing strict decision boundary. */
public final class UnifiedOutcomeMapper {
    private UnifiedOutcomeMapper() { }

    public static UnifiedOutcomeCategory fromDecisionError(
            final ExternalDecisionValidationException.Code code) {
        switch (code) {
        case MISSING_RESPONSE:
        case NULL_RESPONSE:
        case MALFORMED_RESPONSE:
            return UnifiedOutcomeCategory.MALFORMED_RESPONSE;
        case STALE_RESPONSE:
        case DECISION_CONSUMED:
            return UnifiedOutcomeCategory.STALE_RESPONSE;
        case WRONG_ACTOR:
        case WRONG_PRINCIPAL:
            return UnifiedOutcomeCategory.WRONG_ACTOR;
        case ILLEGAL_OPTION:
        case INVALID_SELECTION_COUNT:
        case CANCEL_NOT_ALLOWED:
            return UnifiedOutcomeCategory.ILLEGAL_RESPONSE;
        case TIMEOUT:
            return UnifiedOutcomeCategory.TIMEOUT;
        case UNSUPPORTED_DECISION_PATH:
            return UnifiedOutcomeCategory.UNSUPPORTED_DECISION_PATH;
        default:
            throw new IllegalStateException("untyped decision failure: " + code.name());
        }
    }

    public static UnifiedOutcomeCategory fromTape(final ExternalDecisionTape.ResponseStatus status,
                                                   final String errorCode,
                                                   final boolean explicitCancel) {
        if (status == ExternalDecisionTape.ResponseStatus.ACCEPTED) {
            return explicitCancel ? UnifiedOutcomeCategory.PLAYER_CANCELLED : UnifiedOutcomeCategory.SUCCESS;
        }
        if (errorCode == null) {
            throw new IllegalStateException("failed decision event has no typed error code");
        }
        return fromDecisionError(ExternalDecisionValidationException.Code.valueOf(errorCode));
    }
}
