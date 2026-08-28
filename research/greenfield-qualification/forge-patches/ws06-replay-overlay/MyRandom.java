/* WS06 qualification overlay: explicit game-scoped named RNG streams. */
package forge.util;

import java.security.SecureRandom;
import java.util.Map;
import java.util.Random;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Forge random wrapper plus WS06 process-isolated game-scoped deterministic
 * streams. Legacy callers retain the stock provider only outside an active
 * strict WS06 game scope. Decision-relevant in-game callers must use an
 * explicit named-stream overload, except for qualified transitive Forge-core
 * helpers whose rules caller is proven on the current stack.
 */
public class MyRandom {
    private static Random random = new SecureRandom();

    @FunctionalInterface
    public interface EventObserver {
        void onEvent(RngEvent event);
    }

    @FunctionalInterface
    public interface ReplayProvider {
        int next(RngRequest request);
    }

    public static final class RngRequest {
        private final long eventId;
        private final String gameId;
        private final String stream;
        private final long drawIndex;
        private final int bits;
        private final int generatedValue;

        private RngRequest(long eventId, String gameId, String stream, long drawIndex, int bits, int generatedValue) {
            this.eventId = eventId;
            this.gameId = gameId;
            this.stream = stream;
            this.drawIndex = drawIndex;
            this.bits = bits;
            this.generatedValue = generatedValue;
        }

        public long getEventId() { return eventId; }
        public String getGameId() { return gameId; }
        public String getStream() { return stream; }
        public long getDrawIndex() { return drawIndex; }
        public int getBits() { return bits; }
        public int getGeneratedValue() { return generatedValue; }
    }

    public static final class RngEvent {
        private final long eventId;
        private final String gameId;
        private final String stream;
        private final long drawIndex;
        private final int bits;
        private final int value;

        private RngEvent(long eventId, String gameId, String stream, long drawIndex, int bits, int value) {
            this.eventId = eventId;
            this.gameId = gameId;
            this.stream = stream;
            this.drawIndex = drawIndex;
            this.bits = bits;
            this.value = value;
        }

        public long getEventId() { return eventId; }
        public String getGameId() { return gameId; }
        public String getStream() { return stream; }
        public long getDrawIndex() { return drawIndex; }
        public int getBits() { return bits; }
        public int getValue() { return value; }
    }

    private static final class GameScope {
        private final String gameId;
        private final long seed;
        private final EventObserver observer;
        private final ReplayProvider replayProvider;
        private final AtomicLong eventSequence = new AtomicLong();
        private final Map<String, ScopedRandom> streams = new ConcurrentHashMap<>();

        private GameScope(String gameId, long seed, EventObserver observer, ReplayProvider replayProvider) {
            this.gameId = gameId;
            this.seed = seed;
            this.observer = observer;
            this.replayProvider = replayProvider;
        }
    }

    private static final class ScopedRandom extends Random {
        private static final long serialVersionUID = 1L;
        private final GameScope scope;
        private final String stream;
        private long drawIndex;

        private ScopedRandom(GameScope scope, String stream) {
            super(deriveSeed(scope.seed, scope.gameId, stream));
            this.scope = scope;
            this.stream = stream;
        }

        @Override
        protected int next(int bits) {
            final long eventId = scope.eventSequence.incrementAndGet();
            final long index = drawIndex++;
            final int generated = super.next(bits);
            final RngRequest request = new RngRequest(eventId, scope.gameId, stream, index, bits, generated);
            final int value = scope.replayProvider == null ? generated : scope.replayProvider.next(request);
            final long upperExclusive = 1L << bits;
            if (bits < 32 && (value < 0 || (long) value >= upperExclusive)) {
                throw new IllegalStateException("WS06 replay RNG value outside requested bit width: bits=" + bits + " value=" + value);
            }
            final EventObserver observer = scope.observer;
            if (observer != null) {
                observer.onEvent(new RngEvent(eventId, scope.gameId, stream, index, bits, value));
            }
            return value;
        }
    }

    private static final InheritableThreadLocal<GameScope> threadScope = new InheritableThreadLocal<>();
    private static volatile GameScope processScope;

    public static synchronized void beginGameScope(
            final String gameId,
            final long seed,
            final EventObserver observer,
            final ReplayProvider replayProvider) {
        if (gameId == null || gameId.isBlank()) {
            throw new IllegalArgumentException("WS06 game RNG scope requires non-empty game identity");
        }
        if (processScope != null) {
            throw new IllegalStateException("WS06 game RNG scope is already active");
        }
        final GameScope scope = new GameScope(gameId, seed, observer, replayProvider);
        processScope = scope;
        threadScope.set(scope);
    }

    public static synchronized void endGameScope() {
        threadScope.remove();
        processScope = null;
    }

    public static boolean hasActiveGameScope() {
        return activeScope() != null;
    }

    public static String getActiveGameId() {
        final GameScope scope = activeScope();
        return scope == null ? null : scope.gameId;
    }

    public static void requireActiveGameScope(final String owner) {
        if (activeScope() == null) {
            throw new IllegalStateException("WS06 decision-relevant RNG escaped game scope at " + owner);
        }
    }

    private static GameScope activeScope() {
        final GameScope local = threadScope.get();
        return local != null ? local : processScope;
    }

    public static boolean percentTrue(final int percent) {
        return percent > getRandom().nextInt(100);
    }

    public static boolean percentTrue(final String stream, final int percent) {
        return percent > getRandom(stream).nextInt(100);
    }

    public static Random getRandom() {
        if (Boolean.getBoolean("forge.ws06.strictGameRng") && activeScope() != null) {
            final String bridgedStream = qualifiedTransitiveRulesStream();
            if (bridgedStream == null) {
                throw new IllegalStateException("WS06 unnamed RNG used while a strict game RNG scope is active");
            }
            return getRandom(bridgedStream);
        }
        return random;
    }

    private static String qualifiedTransitiveRulesStream() {
        boolean rulesCaller = false;
        String helperClass = null;
        String helperMethod = null;
        for (final StackTraceElement frame : Thread.currentThread().getStackTrace()) {
            final String className = frame.getClassName();
            if (className.startsWith("forge.game.")) {
                rulesCaller = true;
            }
            if (className.equals("forge.util.Aggregates") || className.equals("forge.util.StreamUtil")) {
                helperClass = className;
                helperMethod = frame.getMethodName();
            }
        }
        if (!rulesCaller || helperClass == null || helperMethod == null) {
            return null;
        }
        return "rules.transitive." + helperClass + "." + helperMethod;
    }

    public static Random getRandom(final String stream) {
        if (stream == null || stream.isBlank()) {
            throw new IllegalArgumentException("WS06 RNG stream name is required");
        }
        final GameScope scope = activeScope();
        if (scope == null) {
            if (Boolean.getBoolean("forge.ws06.strictGameRng")) {
                throw new IllegalStateException("WS06 named rules RNG used without an active game scope: " + stream);
            }
            return random;
        }
        return scope.streams.computeIfAbsent(stream, key -> new ScopedRandom(scope, key));
    }

    public static void setRandom(Random random) {
        MyRandom.random = random;
    }

    public static int[] splitIntoRandomGroups(final int value, final int numGroups) {
        int[] groups = new int[numGroups];
        final Random scoped = getRandom("core.splitIntoRandomGroups");
        for (int i = 0; i < value; i++) {
            groups[scoped.nextInt(numGroups)]++;
        }
        return groups;
    }

    private static long deriveSeed(final long baseSeed, final String gameId, final String stream) {
        long value = baseSeed ^ 0x9E3779B97F4A7C15L;
        value = mixString(value, gameId);
        value = mixString(value, stream);
        return mix64(value);
    }

    private static long mixString(long value, final String text) {
        for (int i = 0; i < text.length(); i++) {
            value ^= text.charAt(i);
            value *= 0x100000001B3L;
            value = Long.rotateLeft(value, 13);
        }
        return value;
    }

    private static long mix64(long z) {
        z = (z ^ (z >>> 30)) * 0xBF58476D1CE4E5B9L;
        z = (z ^ (z >>> 27)) * 0x94D049BB133111EBL;
        return z ^ (z >>> 31);
    }
}
