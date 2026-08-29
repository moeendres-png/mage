package forge.game;

/** Controlled WS21 engine-side failure, distinct from process termination. */
public final class Ws21EngineExecutionException extends RuntimeException {
    private final String faultSite;

    public Ws21EngineExecutionException(final String faultSite) {
        super("controlled engine execution failure");
        this.faultSite = faultSite;
    }

    public String getFaultSite() {
        return faultSite;
    }
}
