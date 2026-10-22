package mage.game.events;

import com.google.common.collect.Sets;
import mage.abilities.Ability;
import mage.game.Controllable;
import mage.game.Game;
import mage.game.permanent.PermanentToken;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * @author TheElk801
 */
public class CreatedTokensEvent extends GameEvent {

    // insertion order: a token has no hashCode, so a HashSet would hand the tokens to triggers in an
    // order that changes from run to run
    private final Set<PermanentToken> createdTokens = new LinkedHashSet<>();

    private CreatedTokensEvent(UUID playerId, Set<PermanentToken> createdTokens, Ability source) {
        super(EventType.CREATED_TOKENS, playerId, source, playerId);
        this.createdTokens.addAll(createdTokens);
    }

    public static void addEvents(Set<PermanentToken> allAddedTokens, Ability source, Game game) {
        allAddedTokens
                .stream()
                .collect(Collectors.toMap(
                        Controllable::getControllerId,
                        Collections::singleton,
                        Sets::union,
                        LinkedHashMap::new
                ))
                .entrySet()
                .stream()
                .map(entry -> new CreatedTokensEvent(entry.getKey(), entry.getValue(), source))
                .forEach(game::addSimultaneousEvent);
    }

    public Set<PermanentToken> getCreatedTokens() {
        return createdTokens;
    }
}
