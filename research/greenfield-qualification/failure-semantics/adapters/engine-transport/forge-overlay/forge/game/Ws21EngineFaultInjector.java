package forge.game;

import java.util.concurrent.atomic.AtomicBoolean;

/**
 * WS21 qualification hook. The injected exception is thrown before the first
 * original statement in GameAction.changeZone. If Forge were to continue after
 * the failed call and enter another changeZone, postFaultBodyReached becomes
 * true and the gate fails closed.
 */
public final class Ws21EngineFaultInjector {
    private static final AtomicBoolean faultFired = new AtomicBoolean();
    private static final AtomicBoolean postFaultBodyReached = new AtomicBoolean();
    private static volatile String faultSite = "";

    private Ws21EngineFaultInjector() { }

    public static void reset() {
        faultFired.set(false);
        postFaultBodyReached.set(false);
        faultSite = "";
    }

    public static void maybeFail(final String site) {
        if (Boolean.getBoolean("ws21.engineFault") && faultFired.compareAndSet(false, true)) {
            faultSite = site;
            throw new Ws21EngineExecutionException(site);
        }
    }

    public static void markOriginalBodyEntry() {
        if (faultFired.get()) {
            postFaultBodyReached.set(true);
        }
    }

    public static boolean faultFired() {
        return faultFired.get();
    }

    public static boolean postFaultBodyReached() {
        return postFaultBodyReached.get();
    }

    public static String faultSite() {
        return faultSite;
    }
}
