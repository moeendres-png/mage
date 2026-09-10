package mage.util;

import java.awt.*;
import java.util.Collection;
import java.util.Random;
import java.util.Set;
import java.util.UUID;

/**
 * WS54 designation: this is the shared NON-RULES random stream (AI exploration and
 * discretionary sampling, UI cosmetics, infrastructure/test randomness).
 *
 * <p>Authoritative Rules randomness lives per game in {@link GameRandom}, owned by the
 * game object and reachable via {@code game.getRulesRandom()}. Production Rules paths
 * must NEVER consume this stream: AI/UI consumption here cannot perturb a credited
 * game's Rules RNG, and {@link #setSeed(long)} is test/non-Rules use only.</p>
 *
 * <p>Created by IGOUDT on 5-9-2016.
 */
public final class RandomUtil {

    private static final Random random = new Random(); // thread safe with seed support, NON-RULES stream

    private RandomUtil() {
    }

    public static Random getRandom() {
        return random;
    }

    public static int nextInt() {
        return random.nextInt();
    }

    public static int nextInt(int max) {
        return random.nextInt(max);
    }

    public static boolean nextBoolean() {
        return random.nextBoolean();
    }

    public static double nextDouble() {
        return random.nextDouble();
    }

    public static Color nextColor() {
        return new Color(RandomUtil.nextInt(256), RandomUtil.nextInt(256), RandomUtil.nextInt(256));
    }

    /**
     * NON-RULES stream seed. Test / AI / infrastructure use only; never use to steer
     * a production Rules path (Rules replay identity comes from the game seed).
     */
    public static void setSeed(long newSeed) {
        random.setSeed(newSeed);
    }

    /**
     * Game-scoped pick: uniform selection from {@code collection} consuming the
     * EXPLICITLY supplied RNG (normally the owning game's Rules RNG). Pure function of
     * (collection iteration order, rng): callers must pass a flow-ordered collection
     * (see WS54 section-18 rule -- never a UUID-hash-ordered HashSet/HashMap view).
     */
    public static <T> T randomFromCollection(Collection<T> collection, Random rng) {
        if (collection.size() < 2) {
            return collection.stream().findFirst().orElse(null);
        }
        int rand = rng.nextInt(collection.size());
        int count = 0;
        for (T current : collection) {
            if (count == rand) {
                return current;
            }
            count++;
        }
        return null;
    }

    public static <T> T randomFromCollection(Collection<T> collection) {
        if (collection.size() < 2) {
            return collection.stream().findFirst().orElse(null);
        }
        int rand = nextInt(collection.size());
        int count = 0;
        for (T current : collection) {
            if (count == rand) {
                return current;
            }
            count++;
        }
        return null;
    }
}
