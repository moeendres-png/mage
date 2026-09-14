package org.mage.test.serverside.ws214;

import mage.constants.RangeOfInfluence;
import mage.game.FakeGame;
import mage.game.Game;
import mage.players.Player;
import mage.util.GameRandom;
import org.junit.FixMethodOrder;
import org.junit.Test;
import org.junit.runners.MethodSorters;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;

import java.io.File;
import java.util.ArrayList;
import java.util.List;

import static org.junit.Assert.*;

/**
 * WS214 TestPlayer Rules-RNG harness qualification (test-only, no production change).
 *
 * <p>Unscripted {@code TestPlayer.flipCoinResult} / {@code rollDieResult} must
 * consume the authoritative per-game {@code game.getRulesRandom()} stream with
 * exactly the production algorithm ({@code nextBoolean()} /
 * {@code nextInt(sides) + 1}), so same seed + same path reproduces across
 * fresh JVMs, different seeds control-diverge, and
 * {@code getRulesRandomCalls} accounts every unscripted draw. Explicitly
 * scripted outcomes ({@code setFlipCoinResult} / {@code setDieRollResult}
 * choice queue) remain exact synthetic test inputs and consume no Rules RNG.</p>
 */
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
public class WS214TestPlayerRulesRngTest {

    private static final long SEED_A = 0x5EED214AL;
    private static final long SEED_B = 0xBEEF214BL;
    private static final int COINS = 16;
    private static final int DICE = 16;
    private static final int DIE_SIDES = 6;

    private static TestPlayer newTestPlayer() {
        return new TestPlayer(new TestComputerPlayer("ws214", RangeOfInfluence.ALL));
    }

    private static Game newSeededGame(long seed) {
        Game game = new FakeGame();
        game.setRulesSeed(seed);
        game.setRequireExplicitSeed(true);
        return game;
    }

    private static List<String> coinDraws(Player player, Game game, int n) {
        List<String> out = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            out.add(player.flipCoinResult(game) ? "H" : "T");
        }
        return out;
    }

    private static List<String> dieDraws(Player player, Game game, int sides, int n) {
        List<String> out = new ArrayList<>(n);
        for (int i = 0; i < n; i++) {
            out.add("d" + player.rollDieResult(sides, game));
        }
        return out;
    }

    private static List<String> mixedDraws(Player player, Game game) {
        List<String> out = new ArrayList<>(COINS + DICE);
        out.addAll(coinDraws(player, game, COINS));
        out.addAll(dieDraws(player, game, DIE_SIDES, DICE));
        return out;
    }

    // Scripted coin outcomes are exact and consume no Rules RNG.
    @Test
    public void t1_scriptedCoinPrecedence() {
        Game game = newSeededGame(SEED_A);
        TestPlayer player = newTestPlayer();
        player.addChoice(TestPlayer.FLIPCOIN_RESULT_TRUE);
        assertTrue(player.flipCoinResult(game));
        player.addChoice(TestPlayer.FLIPCOIN_RESULT_FALSE);
        assertFalse(player.flipCoinResult(game));
        assertTrue(player.getChoices().isEmpty());
        assertEquals("scripted coin outcomes must not consume Rules RNG",
                0L, game.getRulesRandomCalls());
    }

    // Scripted die outcomes are exact and consume no Rules RNG.
    @Test
    public void t2_scriptedDiePrecedence() {
        Game game = newSeededGame(SEED_A);
        TestPlayer player = newTestPlayer();
        player.addChoice(TestPlayer.DIE_ROLL + 4);
        assertEquals(4, player.rollDieResult(DIE_SIDES, game));
        player.addChoice(TestPlayer.DIE_ROLL + 1);
        assertEquals(1, player.rollDieResult(DIE_SIDES, game));
        assertTrue(player.getChoices().isEmpty());
        assertEquals("scripted die outcomes must not consume Rules RNG",
                0L, game.getRulesRandomCalls());
    }

    // Unscripted coins consume the game Rules stream with production semantics.
    @Test
    public void t3_unscriptedCoinUsesRulesStream() {
        Game game = newSeededGame(SEED_A);
        TestPlayer player = newTestPlayer();
        List<String> draws = coinDraws(player, game, 8);
        assertEquals("each unscripted coin must consume exactly one Rules gate",
                8L, game.getRulesRandomCalls());

        GameRandom control = new GameRandom(SEED_A);
        List<String> expected = new ArrayList<>(8);
        for (int i = 0; i < 8; i++) {
            expected.add(control.nextBoolean() ? "H" : "T");
        }
        assertEquals("unscripted coins must equal direct Rules-stream draws", expected, draws);

        Game twin = newSeededGame(SEED_A);
        assertEquals("same seed + same path must reproduce",
                draws, coinDraws(newTestPlayer(), twin, 8));
        assertEquals(8L, twin.getRulesRandomCalls());
    }

    // Unscripted dice consume the game Rules stream with production range semantics.
    @Test
    public void t4_unscriptedDieUsesRulesStream() {
        Game game = newSeededGame(SEED_A);
        TestPlayer player = newTestPlayer();
        List<String> draws = dieDraws(player, game, DIE_SIDES, 8);
        assertEquals("each unscripted die roll must consume exactly one Rules gate",
                8L, game.getRulesRandomCalls());

        GameRandom control = new GameRandom(SEED_A);
        List<String> expected = new ArrayList<>(8);
        for (int i = 0; i < 8; i++) {
            expected.add("d" + (control.nextInt(DIE_SIDES) + 1));
        }
        assertEquals("unscripted dice must equal direct Rules-stream draws", expected, draws);

        Game twin = newSeededGame(SEED_A);
        assertEquals("same seed + same path must reproduce",
                draws, dieDraws(newTestPlayer(), twin, DIE_SIDES, 8));

        // Boundary values: d1 is degenerate-but-exact, d20 stays in range.
        Game bounds = newSeededGame(SEED_A);
        TestPlayer bounded = newTestPlayer();
        for (int i = 0; i < 8; i++) {
            assertEquals(1, bounded.rollDieResult(1, bounds));
        }
        for (int i = 0; i < 32; i++) {
            int roll = bounded.rollDieResult(20, bounds);
            assertTrue("d20 roll out of range: " + roll, roll >= 1 && roll <= 20);
        }
    }

    // Mixed unscripted sequences account every draw on the Rules stream.
    @Test
    public void t5_mixedSequenceAccounting() {
        Game game = newSeededGame(SEED_A);
        List<String> draws = mixedDraws(newTestPlayer(), game);
        assertEquals(COINS + DICE, draws.size());
        assertEquals("mixed coin/die sequence must account every draw",
                (long) (COINS + DICE), game.getRulesRandomCalls());

        Game twin = newSeededGame(SEED_A);
        assertEquals(mixedDraws(newTestPlayer(), twin), draws);
        assertEquals(game.getRulesRandomCalls(), twin.getRulesRandomCalls());
    }

    // Different seeds control the unscripted harness stream.
    @Test
    public void t6_differentSeedControl() {
        Game gameA = newSeededGame(SEED_A);
        List<String> drawsA = mixedDraws(newTestPlayer(), gameA);
        Game gameB = newSeededGame(SEED_B);
        List<String> drawsB = mixedDraws(newTestPlayer(), gameB);
        assertNotEquals("distinct seeds must control unscripted outcomes", drawsA, drawsB);
        assertEquals("consumption shape must be seed-independent",
                gameA.getRulesRandomCalls(), gameB.getRulesRandomCalls());
    }

    // Unscripted TestPlayer behavior equals the production delegate on the same stream.
    @Test
    public void t7_productionParity() {
        Game harnessGame = newSeededGame(SEED_A);
        List<String> harness = mixedDraws(newTestPlayer(), harnessGame);

        Game productionGame = newSeededGame(SEED_A);
        Player production = newTestPlayer().getRealPlayer();
        List<String> productionDraws = mixedDraws(production, productionGame);

        assertEquals("harness unscripted draws must equal the production delegate stream",
                productionDraws, harness);
        assertEquals(harnessGame.getRulesRandomCalls(), productionGame.getRulesRandomCalls());
    }

    // Seed/counter queries never consume Rules RNG.
    @Test
    public void t8_queriesConsumeNothing() {
        Game game = newSeededGame(SEED_A);
        assertEquals(SEED_A, game.getRulesSeed());
        assertTrue(game.isRulesSeedExplicit());
        assertNotNull(game.getRulesRandom());
        assertEquals(0L, game.getRulesRandomCalls());
        mixedDraws(newTestPlayer(), game);
        long after = game.getRulesRandomCalls();
        assertEquals(SEED_A, game.getRulesSeed());
        assertTrue(game.isRulesSeedExplicit());
        assertNotNull(game.getRulesRandom());
        assertEquals("queries must not consume RNG", after, game.getRulesRandomCalls());
    }

    // Fresh-JVM twins: same seed -> identical harness sequence + accounting.
    @Test
    public void t9_freshJvmSameSeedMixedEqual() throws Exception {
        String first = runProbe(SEED_A);
        String second = runProbe(SEED_A);
        System.out.println("WS214-TWIN-A1 " + first);
        System.out.println("WS214-TWIN-A2 " + second);
        assertEquals("fresh-JVM twins with same seed must be identical",
                stripPid(first), stripPid(second));
        assertTrue("fresh game must start unconsumed", first.contains("callsBefore=0"));
        assertTrue("mixed sequence must account every draw",
                first.contains("callsAfter=" + (COINS + DICE)));
        assertEquals("harness sequence must equal the Rules-control sequence",
                field(first, "coins="), field(first, "ctrlCoins="));
        assertEquals(field(first, "dice="), field(first, "ctrlDice="));
    }

    // Fresh-JVM control: different seed -> different harness sequence, same shape.
    @Test
    public void t10_freshJvmDifferentSeedDiverges() throws Exception {
        String digestA = runProbe(SEED_A);
        String digestB = runProbe(SEED_B);
        System.out.println("WS214-CONTROL-A " + digestA);
        System.out.println("WS214-CONTROL-B " + digestB);
        assertNotEquals("distinct seeds must yield distinct harness sequences",
                field(digestA, "coins="), field(digestB, "coins="));
        assertEquals("consumption shape must be seed-independent",
                field(digestA, "callsAfter="), field(digestB, "callsAfter="));
        assertEquals("harness sequence must equal the Rules-control sequence",
                field(digestB, "dice="), field(digestB, "ctrlDice="));
    }

    private static String runProbe(long seed) throws Exception {
        String javaBin = System.getProperty("java.home") + File.separator + "bin" + File.separator + "java";
        ProcessBuilder pb = new ProcessBuilder(
                javaBin, "-cp", System.getProperty("java.class.path"),
                "org.mage.test.serverside.ws214.WS214FreshJvmProbe", Long.toString(seed));
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
            finished = process.waitFor(180, java.util.concurrent.TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("probe interrupted", e);
        }
        assertTrue("probe JVM must finish in time, output:\n" + output, finished);
        assertEquals("probe JVM must exit cleanly, output:\n" + output, 0, process.exitValue());
        for (String line : output.split("\\R")) {
            if (line.startsWith("WS214-PROBE ")) {
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

    private static String stripPid(String digest) {
        StringBuilder kept = new StringBuilder();
        for (String part : digest.split(" ")) {
            if (!part.startsWith("pid=")) {
                if (kept.length() > 0) {
                    kept.append(' ');
                }
                kept.append(part);
            }
        }
        return kept.toString();
    }
}
