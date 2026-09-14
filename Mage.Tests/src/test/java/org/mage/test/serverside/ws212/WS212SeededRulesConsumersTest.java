package org.mage.test.serverside.ws212;

import mage.constants.PhaseStep;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.SmoothedLondonMulligan;
import mage.players.Player;
import org.junit.FixMethodOrder;
import org.junit.Test;
import org.junit.runners.MethodSorters;
import org.mage.test.serverside.base.CardTestCommanderDuelBase;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

import static org.junit.Assert.*;

/**
 * WS212 game-level Rules-RNG seed-authority qualification (real engine game,
 * real decks, genuine production Rules-random operations).
 *
 * <p>Same explicit seed + same decks + same scripted (idle) decisions through the
 * full production path (deck load -&gt; useDeck -&gt; Game.init shuffles -&gt; mulligan
 * flow -&gt; turn flow) must reproduce initial library order, opening hands and
 * Rules-consumption counts; representative in-game consumers (shuffle, coin, die,
 * random discard, smoothed-mulligan draw) must consume the explicit stream and
 * reproduce across twins; distinct seeds must control-diverge. Digests are
 * UUID-agnostic (card names only) and printed as WS212-GAME-DIGEST for
 * cross-process comparison.</p>
 */
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
public class WS212SeededRulesConsumersTest extends CardTestCommanderDuelBase {

    private static final long SEED_A = 0x5EED212AL;
    private static final long SEED_B = 0xBEEF212BL;

    private static String digestA;

    private long runSeed = SEED_A;
    private int stopTurn = 2;

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = super.createNewGameAndPlayers();
        // WS212: credited orchestration input -- explicit seed before init, fail-closed.
        game.setRulesSeed(runSeed);
        game.setRequireExplicitSeed(true);
        return game;
    }

    private void seededRun() {
        try {
            reset();
        } catch (GameException | FileNotFoundException e) {
            throw new IllegalStateException(e);
        }
        setStopAt(stopTurn, PhaseStep.UPKEEP);
        execute();
    }

    private String digest() {
        StringBuilder sb = new StringBuilder();
        sb.append("turn=").append(currentGame.getTurnNum());
        sb.append("|active=").append(nameOf(currentGame.getActivePlayerId()));
        for (Player p : currentGame.getPlayers().values()) {
            sb.append("|player=").append(p.getName());
            sb.append(",life=").append(p.getLife());
            sb.append(",hand=").append(sortedNames(handNames(p)));
            sb.append(",library=").append(String.join("~", libraryNames(p)));
            sb.append(",grave=").append(String.join("~", graveNames(p)));
            sb.append(",battle=").append(sortedNames(battleNames(p)));
        }
        sb.append("|seed=").append(currentGame.getRulesSeed());
        sb.append(",explicit=").append(currentGame.isRulesSeedExplicit());
        sb.append(",calls=").append(currentGame.getRulesRandomCalls());
        return sb.toString();
    }

    private String nameOf(Object id) {
        if (id == null) {
            return "null";
        }
        Player p = currentGame.getPlayer((java.util.UUID) id);
        return p == null ? id.toString() : p.getName();
    }

    private List<String> cardNames(List<java.util.UUID> ids) {
        List<String> names = new ArrayList<>();
        for (java.util.UUID id : ids) {
            mage.cards.Card card = currentGame.getCard(id);
            names.add(card == null ? "null" : card.getName());
        }
        return names;
    }

    private List<String> handNames(Player p) {
        return cardNames(new ArrayList<>(p.getHand()));
    }

    private List<String> libraryNames(Player p) {
        return cardNames(p.getLibrary().getCardList());
    }

    private List<String> graveNames(Player p) {
        return cardNames(new ArrayList<>(p.getGraveyard()));
    }

    private List<String> battleNames(Player p) {
        List<String> names = new ArrayList<>();
        for (mage.game.permanent.Permanent perm : currentGame.getBattlefield().getAllPermanents()) {
            if (perm.isControlledBy(p.getId())) {
                names.add(perm.getName());
            }
        }
        return names;
    }

    private String sortedNames(List<String> names) {
        List<String> copy = new ArrayList<>(names);
        Collections.sort(copy);
        return String.join("~", copy);
    }

    private Player livePlayerA() {
        return currentGame.getPlayer(playerA.getId());
    }

    // Twin capture: initial shuffle + opening hands + consumption count.
    @Test
    public void t1_captureSeedA() {
        seededRun();
        digestA = digest();
        assertTrue("credited seed must be explicit", currentGame.isRulesSeedExplicit());
        assertEquals(SEED_A, currentGame.getRulesSeed());
        assertTrue("init shuffles must consume the Rules stream", currentGame.getRulesRandomCalls() > 0);
        System.out.println("WS212-GAME-DIGEST " + digestA);
    }

    // Same-path twin: fresh game objects, same seed -> identical state + counts.
    @Test
    public void t2_rerunSeedA() {
        seededRun();
        System.out.println("WS212-GAME-DIGEST " + digest());
        assertEquals(digestA, digest());
    }

    // Distinct-seed control: seed demonstrably controls the stream.
    @Test
    public void t3_otherSeedDiverges() {
        runSeed = SEED_B;
        seededRun();
        System.out.println("WS212-GAME-DIGEST(seedB) " + digest());
        assertNotEquals("detector must fire on changed seed", digestA, digest());
    }

    // In-game shuffle reproducibility: the production shuffleLibrary path on twins.
    @Test
    public void t4_inGameShuffleReproducible() {
        seededRun();
        Player player = livePlayerA();
        long callsBefore = currentGame.getRulesRandomCalls();
        player.shuffleLibrary(null, currentGame);
        List<String> libraryAfter = libraryNames(player);
        long callsAfter = currentGame.getRulesRandomCalls();
        assertTrue("in-game shuffle must consume the Rules stream", callsAfter > callsBefore);
        System.out.println("WS212-SHUFFLE-A lib=" + String.join("~", libraryAfter) + " calls=" + callsAfter);

        runSeed = SEED_A;
        seededRun();
        Player twin = livePlayerA();
        long twinBefore = currentGame.getRulesRandomCalls();
        twin.shuffleLibrary(null, currentGame);
        assertEquals("twin shuffle must consume identically", callsAfter - callsBefore,
                currentGame.getRulesRandomCalls() - twinBefore);
        assertEquals("twin shuffle must reproduce library order",
                libraryAfter, libraryNames(twin));
    }

    // Coin/die representatives: scalar Rules draws reproduce across twins.
    //
    // NOTE (harness deviation, documented, not mutated): TestPlayer.flipCoinResult /
    // rollDieResult carry scripted-choice overrides whose UNSCRIPTED fallback consumes
    // the non-Rules RandomUtil stream. Production PlayerImpl consumes
    // game.getRulesRandom(). This test therefore drives the production delegate
    // (TestPlayer.computerPlayer, a genuine PlayerImpl over the live game state),
    // i.e. the exact production methods, bypassing the harness-only fallback.
    @Test
    public void t5_coinAndDieReproducible() {
        seededRun();
        Player player = productionPlayer();
        List<String> drawsA = coinAndDieDraws(player);
        long callsA = currentGame.getRulesRandomCalls();
        System.out.println("WS212-COINDIE-A " + String.join(",", drawsA) + " calls=" + callsA);

        seededRun();
        List<String> drawsB = coinAndDieDraws(productionPlayer());
        assertEquals("twin coin/die sequences must reproduce", drawsA, drawsB);
        assertEquals("twin coin/die consumption must match", callsA, currentGame.getRulesRandomCalls());

        runSeed = SEED_B;
        seededRun();
        List<String> drawsC = coinAndDieDraws(productionPlayer());
        System.out.println("WS212-COINDIE-B " + String.join(",", drawsC));
        assertNotEquals("distinct seed must control coin/die outcomes", drawsA, drawsC);
    }

    private List<String> coinAndDieDraws(Player productionPlayer) {
        List<String> draws = new ArrayList<>();
        for (int i = 0; i < 16; i++) {
            draws.add(productionPlayer.flipCoinResult(currentGame) ? "H" : "T");
        }
        for (int i = 0; i < 16; i++) {
            draws.add("d" + productionPlayer.rollDieResult(6, currentGame));
        }
        return draws;
    }

    private Player productionPlayer() {
        Player testPlayer = livePlayerA();
        try {
            java.lang.reflect.Field field =
                    testPlayer.getClass().getDeclaredField("computerPlayer");
            field.setAccessible(true);
            return (Player) field.get(testPlayer);
        } catch (ReflectiveOperationException e) {
            throw new IllegalStateException("cannot reach TestPlayer production delegate", e);
        }
    }

    // Random-discard representative: getRandomToDiscard path on twins.
    @Test
    public void t6_randomDiscardReproducible() {
        seededRun();
        Player player = livePlayerA();
        List<String> discardedA = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            mage.cards.Card card = player.discardOne(true, false, null, currentGame);
            discardedA.add(card == null ? "null" : card.getName());
        }
        String handAfterA = sortedNames(handNames(player));
        long callsA = currentGame.getRulesRandomCalls();
        System.out.println("WS212-DISCARD-A " + String.join(",", discardedA)
                + " hand=" + handAfterA + " calls=" + callsA);

        seededRun();
        Player twin = livePlayerA();
        List<String> discardedB = new ArrayList<>();
        for (int i = 0; i < 3; i++) {
            mage.cards.Card card = twin.discardOne(true, false, null, currentGame);
            discardedB.add(card == null ? "null" : card.getName());
        }
        assertEquals("twin random discards must reproduce", discardedA, discardedB);
        assertEquals("twin post-discard hands must match",
                handAfterA, sortedNames(handNames(twin)));
        assertEquals("twin discard consumption must match", callsA, currentGame.getRulesRandomCalls());
    }

    // Mulligan representative: smoothed-London drawHand consumes the Rules stream.
    @Test
    public void t7_smoothedMulliganDrawReproducible() {
        seededRun();
        Player player = livePlayerA();
        SmoothedLondonMulligan mulligan = new SmoothedLondonMulligan(0);
        mulligan.drawHand(7, player, currentGame);
        String handA = sortedNames(handNames(player));
        long callsA = currentGame.getRulesRandomCalls();
        System.out.println("WS212-MULLIGAN-A hand=" + handA + " calls=" + callsA);

        seededRun();
        Player twin = livePlayerA();
        new SmoothedLondonMulligan(0).drawHand(7, twin, currentGame);
        assertEquals("twin smoothed-mulligan hands must reproduce",
                handA, sortedNames(handNames(twin)));
        assertEquals("twin mulligan consumption must match", callsA, currentGame.getRulesRandomCalls());
    }

    // Simulation copy on a live game never perturbs the parent stream.
    @Test
    public void t8_liveCopyDoesNotPerturbParent() {
        seededRun();
        long parentCalls = currentGame.getRulesRandomCalls();
        Game copy = currentGame.copy();
        assertTrue(copy.isRulesSeedExplicit());
        assertEquals(currentGame.getRulesSeed(), copy.getRulesSeed());
        assertEquals(parentCalls, copy.getRulesRandomCalls());
        for (int i = 0; i < 50; i++) {
            copy.getRulesRandom().nextInt(1_000_000);
        }
        assertEquals("simulation consumption must not move the parent",
                parentCalls, currentGame.getRulesRandomCalls());
    }
}
