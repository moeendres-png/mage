package mage.util;

import java.util.Random;

/**
 * WS54: authoritative game-scoped Rules RNG.
 *
 * <p>Each authoritative game/session owns exactly one instance. It is NEVER a
 * JVM-global shared stream: game A's consumption cannot alter game B, and AI /
 * UI / test / infrastructure consumption uses the separate non-Rules stream
 * ({@link RandomUtil}) and can never perturb a credited game's Rules randomness.</p>
 *
 * <p>Statistical behavior is intentionally identical to {@link Random} (same 48-bit
 * LCG through the single entropy gate {@link #next(int)}), so the remediation changes
 * control / reproducibility / isolation -- never Magic's random semantics. The engine
 * still actually shuffles (real Fisher-Yates with this RNG at the call sites).</p>
 *
 * <p>Thread safety: all entry points are synchronized. Deterministic consumption ORDER
 * is owned by the single-threaded game lifecycle, not by thread scheduling; never feed
 * this RNG from a parallel stream in a Rules path.</p>
 *
 * <p>Diagnostics only: {@link #getCallsCount()} counts consumed {@code next()} gates
 * since the last seed (wraps at {@link Long#MAX_VALUE}); it is evidence, never authority.</p>
 */
public final class GameRandom extends Random {

    private static final long serialVersionUID = 1L;

    // Same LCG constants as java.util.Random (48-bit seed).
    private static final long MULTIPLIER = 0x5DEECE66DL;
    private static final long ADDEND = 0xBL;
    private static final long MASK = (1L << 48) - 1;

    private long state;
    private long callsCount;
    private double nextNextGaussian;
    private boolean haveNextNextGaussian;

    public GameRandom(long seed) {
        super(0L); // super state unused; this class owns `state` directly
        setSeed(seed);
    }

    /**
     * Resets the stream to an explicit seed (replay identity). Clears the gaussian
     * cache and the consumption counter, exactly like a fresh instance.
     */
    @Override
    public synchronized void setSeed(long seed) {
        this.state = (seed ^ MULTIPLIER) & MASK;
        this.callsCount = 0;
        this.haveNextNextGaussian = false;
        this.nextNextGaussian = 0.0d;
    }

    /**
     * Sole entropy gate. All Random methods (nextInt/nextLong/nextBoolean/nextDouble/
     * nextFloat/nextBytes/nextGaussian and Collections.shuffle) funnel through here.
     */
    @Override
    protected synchronized int next(int bits) {
        state = (state * MULTIPLIER + ADDEND) & MASK;
        if (callsCount < Long.MAX_VALUE) {
            callsCount++;
        }
        return (int) (state >>> (48 - bits));
    }

    /**
     * Exact-state duplicate WITHOUT consuming this instance: the child starts at the
     * parent's current position (sibling sims from one parent draw identically -- a
     * documented AI-search heuristic limitation, never written back to the parent).
     */
    public synchronized GameRandom copy() {
        GameRandom child = new GameRandom(0L);
        child.state = this.state;
        child.callsCount = this.callsCount;
        child.nextNextGaussian = this.nextNextGaussian;
        child.haveNextNextGaussian = this.haveNextNextGaussian;
        return child;
    }

    /**
     * Consumption counter since the last seed (diagnostics / reexecution evidence only).
     */
    public synchronized long getCallsCount() {
        return callsCount;
    }
}
