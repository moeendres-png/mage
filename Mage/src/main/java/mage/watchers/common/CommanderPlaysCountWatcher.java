package mage.watchers.common;

import mage.constants.CommanderCardType;
import mage.constants.WatcherScope;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.events.GameEvent.EventType;
import mage.players.Player;
import mage.util.CardUtil;
import mage.watchers.Watcher;

import java.util.*;

/**
 * Default game watcher, no need to add it with abilities
 * <p>
 * Calcs commanders play count only from command zone (spell or land)
 * Cards like Remand can put command to hand and cast it without commander tax increase
 *
 * @author JayDi85
 */
public class CommanderPlaysCountWatcher extends Watcher {

    private final Map<UUID, Integer> playsCount = new HashMap<>();
    private final Map<UUID, Integer> playerCount = new HashMap<>();

    /**
     * Game default watcher
     */
    public CommanderPlaysCountWatcher() {
        super(WatcherScope.GAME);
    }

    @Override
    public void watch(GameEvent event, Game game) {
        if (event.getType() != EventType.LAND_PLAYED
                && event.getType() != EventType.SPELL_CAST) {
            return;
        }

        // must control main cards (split/mdf cards support)
        final UUID objectId;
        if (event.getType() == EventType.LAND_PLAYED) {
            objectId = CardUtil.getMainCardId(game, event.getTargetId());
        } else if (event.getType() == EventType.SPELL_CAST) {
            objectId = CardUtil.getMainCardId(game, event.getSourceId());
        } else {
            objectId = null;
        }

        // must calc all commanders and signature spell cause uses in commander tax
        boolean isCommanderObject = game
                .getPlayerList()
                .stream()
                .map(game::getPlayer)
                .map(player -> game.getCommandersIds(player, CommanderCardType.ANY, false))
                .flatMap(Collection::stream)
                .anyMatch(id -> Objects.equals(id, objectId));
        if (!isCommanderObject || event.getZone() != Zone.COMMAND) {
            return;
        }
        playsCount.putIfAbsent(objectId, 0);
        playsCount.computeIfPresent(objectId, (u, i) -> i + 1);
        playerCount.putIfAbsent(event.getPlayerId(), 0);
        playerCount.compute(event.getPlayerId(), (u, i) -> i + 1);
    }

    public int getPlaysCount(UUID commanderId) {
        return this.playsCount.getOrDefault(commanderId, 0);
    }

    public int getPlayerCount(UUID playerId) {
        return this.playerCount.getOrDefault(playerId, 0);
    }

    /**
     * Returns an immutable copy of the command-zone cast history currently
     * stored in this Rules-Core watcher.
     */
    public CommanderPlaysCountState getStateForGameLoad() {
        return CommanderPlaysCountState.fromMap(this.playsCount);
    }

    /**
     * Restore canonical command-zone cast history as part of an explicit game
     * state load.
     *
     * <p>This method does not emit SPELL_CAST, LAND_PLAYED, trigger, or other
     * historical game events. It validates every supplied object id against
     * XMage's current native commander mapping and derives the player aggregate
     * from that mapping. Runtime event processing remains unchanged and will
     * increment the restored counts normally on later real command-zone casts.</p>
     *
     * <p>This is intentionally a narrow state-restoration API, not a gameplay
     * counter setter.</p>
     *
     * @throws IllegalArgumentException if an id is not a current native
     * commander/signature object, a commander is mapped to multiple players,
     * or aggregate integer arithmetic overflows
     */
    public void restoreStateForGameLoad(CommanderPlaysCountState restoredState, Game game) {
        Objects.requireNonNull(restoredState, "restoredState");
        Objects.requireNonNull(game, "game");

        Map<UUID, UUID> commanderToPlayer = new HashMap<>();
        for (UUID playerId : game.getPlayerList()) {
            Player player = game.getPlayer(playerId);
            if (player == null) {
                continue;
            }
            for (UUID commanderId : game.getCommandersIds(player, CommanderCardType.ANY, false)) {
                UUID previousPlayerId = commanderToPlayer.putIfAbsent(commanderId, playerId);
                if (previousPlayerId != null && !previousPlayerId.equals(playerId)) {
                    throw new IllegalArgumentException(
                            "Commander object is mapped to multiple players: " + commanderId
                    );
                }
            }
        }

        Map<UUID, Integer> restoredPlaysCount = new HashMap<>();
        Map<UUID, Integer> restoredPlayerCount = new HashMap<>();
        for (Map.Entry<UUID, Integer> entry : restoredState.getCommanderCounts().entrySet()) {
            UUID commanderId = entry.getKey();
            int count = entry.getValue();
            UUID playerId = commanderToPlayer.get(commanderId);
            if (playerId == null) {
                throw new IllegalArgumentException(
                        "Unknown, stale, or non-commander object id in commander history: " + commanderId
                );
            }
            restoredPlaysCount.put(commanderId, count);
            if (count > 0) {
                restoredPlayerCount.merge(playerId, count, Math::addExact);
            }
        }

        this.playsCount.clear();
        this.playsCount.putAll(restoredPlaysCount);
        this.playerCount.clear();
        this.playerCount.putAll(restoredPlayerCount);
    }
}
