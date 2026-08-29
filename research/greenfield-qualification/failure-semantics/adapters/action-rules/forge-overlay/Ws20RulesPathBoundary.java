package forge.game;

/**
 * Authoritative Rules Core fail-closed boundary for rule conditions that Forge
 * explicitly does not model correctly.
 */
public final class Ws20RulesPathBoundary {
    private Ws20RulesPathBoundary() { }

    /**
     * Exact guard called from GameAction.changeZone inside the Astrotorium
     * zone-change branch. The Rules Core supplies the live merged-object
     * condition; no adapter or pilot chooses a substitute resolution.
     */
    public static void requireSupportedAstrotoriumMergedZoneChange(final String gameId,
                                                                   final int principalId,
                                                                   final boolean mergedObject) {
        if (mergedObject) {
            throw new Ws20FailureException(
                    Ws20FailureSignal.unsupportedRulesPath(gameId, principalId));
        }
    }
}