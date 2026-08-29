package forge.gamemodes.match.input;

import java.util.EnumSet;
import java.util.concurrent.atomic.AtomicInteger;

/** Exact-pin executable witness for unified typed outcomes and no fallback. */
public final class Ws12FailureSemanticsContractTest {
    private static void require(final boolean condition, final String message) {
        if (!condition) { throw new AssertionError(message); }
    }

    public static void main(final String[] args) {
        require(UnifiedOutcomeCategory.values().length == 16, "authoritative category count changed");
        require(EnumSet.allOf(UnifiedOutcomeCategory.class).contains(UnifiedOutcomeCategory.UNSUPPORTED_RULES_PATH),
                "unsupported rules path is not typed");
        for (final ExternalDecisionValidationException.Code code
                : ExternalDecisionValidationException.Code.values()) {
            require(UnifiedOutcomeMapper.fromDecisionError(code) != null,
                    "unmapped decision error: " + code.name());
        }

        final AtomicInteger state = new AtomicInteger(7);
        for (final UnifiedOutcomeCategory category : UnifiedOutcomeCategory.values()) {
            final int before = state.get();
            final UnifiedOutcome outcome;
            if (category == UnifiedOutcomeCategory.SUCCESS) {
                state.incrementAndGet(); // commit only an already accepted authoritative plan
                outcome = UnifiedOutcome.success("corr:success", "game:1", 91L, 1);
                require(state.get() == before + 1, "SUCCESS did not commit exactly once");
            } else {
                outcome = UnifiedOutcome.failure(category, "corr:" + category.name(), "game:1", 91L, 1);
                require(state.get() == before, category.name() + " mutated state or applied a fallback");
            }
            require(outcome.getCategory() == category, "outcome was coerced to another category");
            require(!outcome.getPublicMessage().contains("opponent-hand-secret"),
                    "public failure payload leaked hidden information");
        }

        require(UnifiedOutcomeMapper.fromTape(ExternalDecisionTape.ResponseStatus.ACCEPTED, null, true)
                == UnifiedOutcomeCategory.PLAYER_CANCELLED, "explicit legal cancel is not distinct");
        require(UnifiedOutcomeMapper.fromTape(ExternalDecisionTape.ResponseStatus.ACCEPTED, null, false)
                == UnifiedOutcomeCategory.SUCCESS, "success is not distinct");
        System.out.println("WS12_JAVA_FAILURE_SEMANTICS=PASS");
    }
}
