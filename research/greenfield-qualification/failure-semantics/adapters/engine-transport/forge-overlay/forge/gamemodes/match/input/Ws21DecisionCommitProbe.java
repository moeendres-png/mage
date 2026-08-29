package forge.gamemodes.match.input;

import java.util.concurrent.atomic.AtomicLong;

/** Non-sensitive counters proving where a WS21 decision stopped. */
public final class Ws21DecisionCommitProbe {
    private static final AtomicLong opened = new AtomicLong();
    private static final AtomicLong validated = new AtomicLong();
    private static final AtomicLong applied = new AtomicLong();
    private static final AtomicLong transportPropagated = new AtomicLong();
    private static volatile long lastDecisionId = -1L;
    private static volatile int lastPrincipalId = -1;
    private static volatile String lastTransportStage = "";

    private Ws21DecisionCommitProbe() { }

    public static void reset() {
        opened.set(0L);
        validated.set(0L);
        applied.set(0L);
        transportPropagated.set(0L);
        lastDecisionId = -1L;
        lastPrincipalId = -1;
        lastTransportStage = "";
    }

    public static void recordOpen(final ExternalDecisionRequest request) {
        opened.incrementAndGet();
        lastDecisionId = request.getDecisionId();
        lastPrincipalId = request.getPrincipalId();
    }

    public static void recordValidated(final ExternalDecisionRequest request) {
        validated.incrementAndGet();
        lastDecisionId = request.getDecisionId();
        lastPrincipalId = request.getPrincipalId();
    }

    public static void recordApplied(final long decisionId, final int principalId) {
        applied.incrementAndGet();
        lastDecisionId = decisionId;
        lastPrincipalId = principalId;
    }

    public static void recordTransportPropagation(final ExternalDecisionRequest request,
                                                  final ExternalDecisionTransportException failure) {
        transportPropagated.incrementAndGet();
        lastDecisionId = request.getDecisionId();
        lastPrincipalId = request.getPrincipalId();
        lastTransportStage = failure.getStage().name();
    }

    public static long opened() { return opened.get(); }
    public static long validated() { return validated.get(); }
    public static long applied() { return applied.get(); }
    public static long transportPropagated() { return transportPropagated.get(); }
    public static long lastDecisionId() { return lastDecisionId; }
    public static int lastPrincipalId() { return lastPrincipalId; }
    public static String lastTransportStage() { return lastTransportStage; }
}
