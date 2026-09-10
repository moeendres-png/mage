package org.mage.test.serverside.ws54;

import mage.constants.PhaseStep;
import mage.game.Game;
import mage.game.GameException;
import mage.players.Player;
import mage.util.RandomUtil;
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
 * WS54 game-level reexecution gates (real engine game, real cards, genuine
 * production Rules-random operations: init library shuffles, choosing-player
 * pick, mulligan flow).
 *
 * <p>Same seed + same decks + same scripted (idle) decisions run through the full
 * production path: deck load -&gt; useDeck -&gt; Game.init shuffles -&gt; turn flow.
 * Digests are UUID-agnostic (card names only) and printed as WS54-GAME-DIGEST for
 * fresh-process comparison.</p>
 */
@FixMethodOrder(MethodSorters.NAME_ASCENDING)
public class WS54SeededReexecutionTest extends CardTestCommanderDuelBase {

    private static final long SEED_A = 0x5EED1234L;
    private static final long SEED_B = 0xBEEF9999L;

    private static String digestA;

    private long runSeed = SEED_A;
    private int stopTurn = 2;

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = super.createNewGameAndPlayers();
        // WS54: credited orchestration input -- explicit seed before init, fail-closed.
        // NOTE: the harness @Before reset() also calls this before the test body runs,
        // so every method below re-invokes reset() AFTER fixing runSeed (see seededRun).
        game.setRulesSeed(runSeed);
        game.setRequireExplicitSeed(true);
        return game;
    }

    /**
     * Fixes the seed, then re-creates the game through the harness reset path so the
     * explicit seed lands before init. Uniform for all methods (the @Before-created
     * game is discarded).
     */
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

    // P1-game/P6: same seed + same input, full production path -> identical semantic state.
    @Test
    public void t1_captureSeedA() {
        seededRun();
        digestA = digest();
        assertTrue("credited seed must be explicit", currentGame.isRulesSeedExplicit());
        assertEquals(SEED_A, currentGame.getRulesSeed());
        assertTrue("init shuffles must consume the Rules stream", currentGame.getRulesRandomCalls() > 0);
        System.out.println("WS54-GAME-DIGEST " + digestA);
    }

    // Same-JVM reexecution: fresh game objects, same seed -> same digest.
    @Test
    public void t2_rerunSeedA() {
        seededRun();
        System.out.println("WS54-GAME-DIGEST " + digest());
        assertEquals(digestA, digest());
    }

    // P2-game + negative seed control: different fixed seed -> different digest.
    @Test
    public void t3_otherSeedDiverges() {
        runSeed = SEED_B;
        seededRun();
        System.out.println("WS54-GAME-DIGEST(seedB) " + digest());
        assertNotEquals("detector must fire on changed seed", digestA, digest());
    }

    // P3-game: after a full foreign-seed game ran in this JVM, seed A reproduces exactly.
    @Test
    public void t4_rerunAfterOtherSeed() {
        seededRun();
        assertEquals("foreign-seed game must not perturb reexecution", digestA, digest());
    }

    // P4-game: a non-Rules RNG storm around (and natural AI global use during) the live
    // game must not perturb the credited Rules stream.
    @Test
    public void t5_nonRulesStorm() {
        RandomUtil.setSeed(987654321L);
        for (int i = 0; i < 50_000; i++) {
            RandomUtil.nextInt(1_000_000);
        }
        seededRun();
        assertEquals("non-Rules consumption must not perturb Rules reexecution", digestA, digest());
    }

    // Negative decision control: an authoritative decision change is detected.
    @Test
    public void t6_decisionChangeDiverges() {
        runSeed = SEED_A;
        try {
            reset();
        } catch (GameException | FileNotFoundException e) {
            throw new IllegalStateException(e);
        }
        setStopAt(stopTurn, PhaseStep.UPKEEP);
        concede(1, PhaseStep.UPKEEP, playerA);
        execute();
        System.out.println("WS54-GAME-DIGEST(concede) " + digest());
        assertNotEquals("detector must fire on changed authoritative decision", digestA, digest());
    }

    // Negative progression control: a longer run is detected (digest is no constant).
    @Test
    public void t7_progressionChangeDiverges() {
        stopTurn = 3;
        seededRun();
        System.out.println("WS54-GAME-DIGEST(turn3) " + digest());
        assertNotEquals("detector must fire on changed progression", digestA, digest());
    }
}
