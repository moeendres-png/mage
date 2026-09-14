package org.mage.test.serverside.ws214;

import mage.constants.RangeOfInfluence;
import mage.game.FakeGame;
import mage.game.Game;
import mage.util.GameRandom;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;

import java.util.ArrayList;
import java.util.List;

/**
 * WS214 fresh-JVM probe (harness-only, Mage.Tests test sourceset).
 *
 * <p>Drives the unscripted {@code TestPlayer.flipCoinResult} /
 * {@code TestPlayer.rollDieResult} path (no scripted choices queued) on a fresh
 * {@link FakeGame} with an explicit rules seed, then prints one digest line
 * ({@code WS214-PROBE ...}) binding the explicit seed, the TestPlayer coin/die
 * sequences, the Rules-consumption count, and a direct
 * {@code game.getRulesRandom()} control sequence drawn from a second
 * same-seed game. Process identity (pid) is diagnostic metadata only.</p>
 *
 * <p>Pre-fix the unscripted fallback consumes the shared non-Rules
 * {@code RandomUtil} stream: two same-seed processes print equal Rules-control
 * sequences and equal call counts while the TestPlayer sequences differ.
 * Post-fix the TestPlayer sequences must equal the Rules-control sequence
 * (same seed, same algorithm, same call order) across fresh JVMs.</p>
 */
public final class WS214FreshJvmProbe {

    private static final int COINS = 16;
    private static final int DICE = 16;
    private static final int DIE_SIDES = 6;

    private WS214FreshJvmProbe() {
    }

    public static void main(String[] args) {
        long seed = Long.parseLong(args[0]);

        Game game = new FakeGame();
        game.setRulesSeed(seed);
        game.setRequireExplicitSeed(true);
        long callsBefore = game.getRulesRandomCalls();

        TestPlayer player = new TestPlayer(new TestComputerPlayer("ws214-probe", RangeOfInfluence.ALL));

        List<String> coins = new ArrayList<>(COINS);
        for (int i = 0; i < COINS; i++) {
            coins.add(player.flipCoinResult(game) ? "H" : "T");
        }
        List<String> dice = new ArrayList<>(DICE);
        for (int i = 0; i < DICE; i++) {
            dice.add("d" + player.rollDieResult(DIE_SIDES, game));
        }
        long callsAfter = game.getRulesRandomCalls();

        // Direct Rules-stream control: same seed, same algorithm, same call order.
        GameRandom control = new GameRandom(seed);
        List<String> ctrlCoins = new ArrayList<>(COINS);
        for (int i = 0; i < COINS; i++) {
            ctrlCoins.add(control.nextBoolean() ? "H" : "T");
        }
        List<String> ctrlDice = new ArrayList<>(DICE);
        for (int i = 0; i < DICE; i++) {
            ctrlDice.add("d" + (control.nextInt(DIE_SIDES) + 1));
        }

        long pid = pidOfCurrentJvm();
        System.out.println("WS214-PROBE"
                + " seed=" + game.getRulesSeed()
                + " explicit=" + game.isRulesSeedExplicit()
                + " coins=" + String.join(",", coins)
                + " dice=" + String.join(",", dice)
                + " callsBefore=" + callsBefore
                + " callsAfter=" + callsAfter
                + " ctrlCoins=" + String.join(",", ctrlCoins)
                + " ctrlDice=" + String.join(",", ctrlDice)
                + " pid=" + pidOfCurrentJvm());
    }

    /**
     * Java-8-compatible pid for diagnostic metadata (test sourceset targets release 8).
     */
    private static long pidOfCurrentJvm() {
        String name = java.lang.management.ManagementFactory.getRuntimeMXBean().getName();
        int at = name.indexOf('@');
        try {
            return Long.parseLong(at > 0 ? name.substring(0, at) : name);
        } catch (NumberFormatException e) {
            return -1L;
        }
    }
}
