package mage.watchers.common;

import java.io.Serializable;
import java.util.Collection;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/**
 * Immutable state-load snapshot for command-zone commander cast history.
 *
 * <p>This is Rules-Core state. It intentionally stores only per-commander
 * counts. {@link CommanderPlaysCountWatcher} derives the per-player aggregate
 * from the current game's native commander ownership mapping when the snapshot
 * is restored, so callers cannot inject mutually inconsistent aggregates.</p>
 *
 * <p>The snapshot is not a gameplay action and does not represent historical
 * SPELL_CAST or LAND_PLAYED events.</p>
 */
public final class CommanderPlaysCountState implements Serializable {

    private final Map<UUID, Integer> commanderCounts;

    /**
     * Build a state snapshot from explicit entries.
     *
     * @throws IllegalArgumentException on duplicate commander ids or negative counts
     * @throws NullPointerException on null entries, ids or counts
     */
    public CommanderPlaysCountState(Collection<Count> counts) {
        Objects.requireNonNull(counts, "counts");
        Map<UUID, Integer> copy = new LinkedHashMap<>();
        for (Count count : counts) {
            Objects.requireNonNull(count, "count");
            UUID commanderId = Objects.requireNonNull(count.getCommanderId(), "commanderId");
            int value = count.getCount();
            if (value < 0) {
                throw new IllegalArgumentException("Commander cast count cannot be negative: " + value);
            }
            if (copy.putIfAbsent(commanderId, value) != null) {
                throw new IllegalArgumentException("Duplicate commander cast history entry: " + commanderId);
            }
        }
        this.commanderCounts = Collections.unmodifiableMap(copy);
    }

    /**
     * Convenience factory for callers that already have a unique-id map.
     */
    public static CommanderPlaysCountState fromMap(Map<UUID, Integer> counts) {
        Objects.requireNonNull(counts, "counts");
        Map<UUID, Integer> copy = new LinkedHashMap<>();
        counts.forEach((commanderId, count) -> {
            Objects.requireNonNull(commanderId, "commanderId");
            Objects.requireNonNull(count, "count");
            if (count < 0) {
                throw new IllegalArgumentException("Commander cast count cannot be negative: " + count);
            }
            copy.put(commanderId, count);
        });
        return new CommanderPlaysCountState(
                copy.entrySet().stream()
                        .map(entry -> new Count(entry.getKey(), entry.getValue()))
                        .toList()
        );
    }

    public Map<UUID, Integer> getCommanderCounts() {
        return commanderCounts;
    }

    public int getPlaysCount(UUID commanderId) {
        return commanderCounts.getOrDefault(commanderId, 0);
    }

    /**
     * One canonical commander-history entry.
     */
    public static final class Count implements Serializable {

        private final UUID commanderId;
        private final int count;

        public Count(UUID commanderId, int count) {
            this.commanderId = Objects.requireNonNull(commanderId, "commanderId");
            if (count < 0) {
                throw new IllegalArgumentException("Commander cast count cannot be negative: " + count);
            }
            this.count = count;
        }

        public UUID getCommanderId() {
            return commanderId;
        }

        public int getCount() {
            return count;
        }
    }
}
