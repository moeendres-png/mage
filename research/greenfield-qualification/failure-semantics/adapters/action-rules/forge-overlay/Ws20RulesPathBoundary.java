package forge.game;

/**
 * Authoritative Rules Core fail-closed boundary for rule conditions that Forge
 * explicitly does not model correctly.
 */
public final class Ws20RulesPathBoundary {
    private Ws20RulesPathBoundary() { }

    /**
     * The caller uses this only inside the Astrotorium merged-object TODO path.
     * The generic return type lets the Rules Core replace the old heuristic
     * return expression without inventing a substitute game object.
     */
    public static <T> T unsupportedAstrotoriumMergedZoneChange(final String gameId,
                                                               final int principalId) {
        throw new Ws20FailureException(
                Ws20FailureSignal.unsupportedRulesPath(gameId, principalId));
    }
}