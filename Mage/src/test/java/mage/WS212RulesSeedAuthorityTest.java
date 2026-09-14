package mage;

import mage.game.FakeGame;
import mage.game.Game;
import mage.util.GameRandom;
import mage.util.RandomUtil;
import org.junit.Test;

import java.io.File;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

import static org.junit.Assert.*;

/**
 * WS212 engine-side Rules-RNG seed-authority qualification (Mage module, no card DB).
 *
 * <p>Qualifies the adjudicated contract
 * ({@code EXISTING_CORE_API_SUFFICIENT_NEEDS_TEST_HARDENING}): explicit seed
 * required + absent fails before consumption; explicit seed before start is
 * accepted; same-seed fresh-JVM twins reproduce initial shuffle + opening hand +
 * consumption count; distinct seeds control; reseed resets stream/counter;
 * default seed recorded but non-explicit; queries consume nothing;
 * {@code RandomUtil} cannot steer the Rules stream; copies isolate the parent.</p>
 */
public class WS212RulesSeedAuthorityTest {

    private static final long SEED_A = 0x5EED212AL;
    private static final long SEED_B = 0xBEEF212BL;

    // 1. explicit seed required + absent -> fail BEFORE any random consumption.
    @Test
    public void testRequireExplicitSeedAbsentFailsClosedBeforeConsumption() throws Exception {
        Game game = new FakeGame();
        game.setRequireExplicitSeed(true);
        assertFalse(game.isRulesSeedExplicit());
        assertEquals(0L, game.getRulesRandomCalls());
        java.lang.reflect.Method init = game.getClass().getSuperclass()
                .getDeclaredMethod("init", UUID.class);
        init.setAccessible(true);
        try {
            init.invoke(game, UUID.randomUUID());
            fail("credited init without an explicit seed must fail closed");
        } catch (java.lang.reflect.InvocationTargetException e) {
            assertTrue("expected IllegalStateException, got " + e.getCause(),
                    e.getCause() instanceof IllegalStateException);
        }
        assertEquals("failed init must not consume Rules randomness",
                0L, game.getRulesRandomCalls());
    }

    // 2. explicit seed set before start -> accepted; queries consume nothing.
    @Test
    public void testExplicitSeedSetBeforeStartAcceptedAndQueriesFree() {
        Game game = new FakeGame();
        game.setRulesSeed(SEED_A);
        game.setRequireExplicitSeed(true);
        assertTrue(game.isRulesSeedExplicit());
        assertEquals(SEED_A, game.getRulesSeed());
        assertEquals(0L, game.getRulesRandomCalls());
        // Queries must not consume RNG.
        assertEquals(SEED_A, game.getRulesSeed());
        assertTrue(game.isRulesSeedExplicit());
        assertEquals(0L, game.getRulesRandomCalls());
        assertNotNull(game.getRulesRandom());
        assertEquals(0L, game.getRulesRandomCalls());
        // One draw consumes exactly one gate (nextBoolean funnels a single next() call).
        game.getRulesRandom().nextBoolean();
        assertEquals(1L, game.getRulesRandomCalls());
    }

    // 7. reseed resets stream/counter as the contract permits (before game start).
    @Test
    public void testReseedResetsStreamAndCounter() {
        Game game = new FakeGame();
        game.setRulesSeed(SEED_A);
        List<Integer> first = draws(game.getRulesRandom(), 8);
        assertEquals(8L, game.getRulesRandomCalls());
        game.setRulesSeed(SEED_A);
        assertEquals(0L, game.getRulesRandomCalls());
        assertEquals("same reseed must restart the identical stream",
                first, draws(game.getRulesRandom(), 8));
        game.setRulesSeed(SEED_B);
        assertEquals(0L, game.getRulesRandomCalls());
        assertTrue(game.isRulesSeedExplicit());
    }

    // 8. default seed recorded but explicit flag false.
    @Test
    public void testDefaultSeedRecordedButNotExplicit() {
        Game game = new FakeGame();
        assertNotNull(game.getRulesRandom());
        assertFalse("default construction must be non-credited", game.isRulesSeedExplicit());
        assertEquals(0L, game.getRulesRandomCalls());
        // Recorded identity exists (a seed is carried even without explicit supply).
        long recorded = game.getRulesSeed();
        game.getRulesRandom().nextInt(10);
        assertEquals(recorded, game.getRulesSeed());
        assertEquals(1L, game.getRulesRandomCalls());
        assertFalse(game.isRulesSeedExplicit());
    }

    // RandomUtil storm must not steer the authoritative Rules stream.
    @Test
    public void testNonRulesStormCannotPerturbRulesStream() {
        Game game = new FakeGame();
        game.setRulesSeed(SEED_A);
        int first = game.getRulesRandom().nextInt(1_000_000);
        RandomUtil.setSeed(0x12345L);
        for (int i = 0; i < 10_000; i++) {
            RandomUtil.nextInt(1_000_000);
            RandomUtil.nextBoolean();
            RandomUtil.nextDouble();
        }
        GameRandom control = new GameRandom(SEED_A);
        control.nextInt(1_000_000);
        assertEquals("Rules stream must be immune to non-Rules consumption",
                control.nextInt(1_000_000), game.getRulesRandom().nextInt(1_000_000));
        assertEquals(first, new GameRandom(SEED_A).nextInt(1_000_000));
    }

    // 12. simulation copy duplicates state but never perturbs the parent.
    @Test
    public void testSimulationCopyDoesNotPerturbParent() {
        Game game = new FakeGame();
        game.setGameOptions(new mage.game.GameOptions());
        game.setRulesSeed(SEED_A);
        game.getRulesRandom().nextInt(1_000_000);
        game.getRulesRandom().nextInt(1_000_000);
        Game copy = game.copy();
        assertTrue(copy.isRulesSeedExplicit());
        assertEquals(SEED_A, copy.getRulesSeed());
        assertEquals(game.getRulesRandomCalls(), copy.getRulesRandomCalls());
        // Sibling starts at the parent's current position by design (documented).
        assertEquals(game.getRulesRandom().nextInt(1_000_000),
                copy.getRulesRandom().nextInt(1_000_000));
        // Heavy simulation consumption on the copy...
        for (int i = 0; i < 100; i++) {
            copy.getRulesRandom().nextInt(1_000_000);
        }
        long before = game.getRulesRandomCalls();
        // ...must not move the parent: parent continues the undisturbed control stream.
        GameRandom control = new GameRandom(SEED_A);
        for (int i = 0; i < 3; i++) {
            control.nextInt(1_000_000);
        }
        assertEquals(control.nextInt(1_000_000), game.getRulesRandom().nextInt(1_000_000));
        assertEquals(before + 1, game.getRulesRandomCalls());
    }

    // 3+4+5. fresh-JVM twins: same seed -> identical shuffle/hand/calls.
    @Test
    public void testFreshJvmTwinsSameSeedIdentical() throws Exception {
        String first = runProbe(SEED_A);
        String second = runProbe(SEED_A);
        System.out.println("WS212-TWIN-A1 " + first);
        System.out.println("WS212-TWIN-A2 " + second);
        assertEquals("fresh-JVM twins with same seed must be identical", first, second);
        assertTrue(first.contains("explicit=true"));
        assertTrue("60-card Fisher-Yates must consume exactly 59 gates",
                first.contains("calls=59"));
    }

    // 6. different-seed control: seed demonstrably controls the stream.
    @Test
    public void testDifferentSeedControlDiverges() throws Exception {
        String digestA = runProbe(SEED_A);
        String digestB = runProbe(SEED_B);
        System.out.println("WS212-CONTROL-A " + digestA);
        System.out.println("WS212-CONTROL-B " + digestB);
        assertNotEquals("distinct seeds must yield distinct shuffles", digestA, digestB);
        // Same declared input in both processes (pre-order bound to the digest).
        assertEquals("pre-shuffle order must match across processes (same input)",
                field(digestA, "pre="), field(digestB, "pre="));
        assertNotEquals(field(digestA, "post="), field(digestB, "post="));
    }

    private static List<Integer> draws(GameRandom rng, int n) {
        List<Integer> out = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            out.add(rng.nextInt(1_000_000));
        }
        return out;
    }

    private static String runProbe(long seed) throws Exception {
        String javaBin = System.getProperty("java.home") + File.separator + "bin" + File.separator + "java";
        ProcessBuilder pb = new ProcessBuilder(
                javaBin, "-cp", System.getProperty("java.class.path"),
                "mage.WS212FreshJvmProbe", Long.toString(seed));
        pb.redirectErrorStream(true);
        Process process = pb.start();
        String output;
        try (java.io.InputStream in = process.getInputStream();
             java.io.ByteArrayOutputStream buffer = new java.io.ByteArrayOutputStream()) {
            byte[] chunk = new byte[8192];
            int read;
            while ((read = in.read(chunk)) != -1) {
                buffer.write(chunk, 0, read);
            }
            output = new String(buffer.toByteArray(), java.nio.charset.StandardCharsets.UTF_8);
        }
        boolean finished;
        try {
            finished = process.waitFor(120, java.util.concurrent.TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("probe interrupted", e);
        }
        assertTrue("probe JVM must finish in time, output:\n" + output, finished);
        assertEquals("probe JVM must exit cleanly, output:\n" + output, 0, process.exitValue());
        for (String line : output.split("\\R")) {
            if (line.startsWith("WS212-PROBE ")) {
                return line.trim();
            }
        }
        fail("probe printed no digest, output:\n" + output);
        throw new IllegalStateException("unreachable");
    }

    private static String field(String digest, String key) {
        for (String part : digest.split(" ")) {
            if (part.startsWith(key)) {
                return part.substring(key.length());
            }
        }
        fail("digest missing field " + key + ": " + digest);
        throw new IllegalStateException("unreachable");
    }
}
