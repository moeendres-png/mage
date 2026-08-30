package forge.game;

import forge.game.spellability.SpellAbility;

/**
 * Simulator-owned semantic assertion hook. Implementations compare captured
 * engine state with an externally supplied actual-card witness; they do not
 * decide legality or resolve Magic rules.
 */
@FunctionalInterface
public interface CardBehaviorVerifier {
    void verify(Game game, SpellAbility resolvedAbility);
}
