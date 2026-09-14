package org.mage.test.serverside.ws211;

import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.GameImpl;
import mage.game.stack.Spell;
import mage.players.Player;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.util.UUID;

/**
 * WS211 — authoritative concession action surface, native 2-player behavior.
 *
 * Uses only pre-existing engine seams (Game.concede / setConcedingPlayer /
 * checkConcede) to characterize current behavior before the availability
 * surface is added. No card behavior under test: concession is a player rule
 * (CR 104.3a), so tests use real running games with direct native calls.
 */
public class WS211ConcessionActionTest extends CardTestPlayerBase {

    @Test
    public void testPriorityPlayerConcedesEndsGame() {
        concede(1, PhaseStep.PRECOMBAT_MAIN, playerA);

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertTrue("game must end when one of two players concedes", currentGame.hasEnded());
        assertWonTheGame(playerB);
        assertLostTheGame(playerA);
    }

    @Test
    public void testNonPriorityPlayerConcedes() {
        // B concedes during A's turn while B has no priority: CR 104.3a "at any time".
        concede(1, PhaseStep.PRECOMBAT_MAIN, playerB);

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertTrue("non-priority concession must take effect", currentGame.hasEnded());
        assertWonTheGame(playerA);
        assertLostTheGame(playerB);
    }

    @Test
    public void testConcedeWithNonemptyStack() {
        addCard(Zone.HAND, playerA, "Lightning Bolt", 1);

        runCode("concede while own spell is on the stack", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> {
                    Player conceder = game.getPlayer(player.getId());
                    Assert.assertNotNull(conceder);
                    Card bolt = null;
                    for (UUID cardId : player.getHand()) {
                        Card candidate = game.getCard(cardId);
                        if (candidate != null && "Lightning Bolt".equals(candidate.getName())) {
                            bolt = candidate;
                            break;
                        }
                    }
                    Assert.assertNotNull("test setup: Lightning Bolt must be in hand", bolt);
                    game.getStack().push(game, new Spell(bolt, bolt.getSpellAbility(), player.getId(), Zone.HAND, game));
                    Assert.assertFalse("test setup: stack must be nonempty", game.getStack().isEmpty());

                    long rngBefore = game.getRulesRandomCalls();
                    game.concede(player.getId());
                    ((GameImpl) game).checkConcede();

                    // 2-player: leave() short-circuits object cleanup once the game is over
                    // (existing intended behavior); stack-object cleanup itself is proven
                    // in the 4-player continuation test where the game goes on.
                    Assert.assertEquals("concession must not consume Rules RNG",
                            rngBefore, game.getRulesRandomCalls());
                    Assert.assertTrue(game.getPlayer(player.getId()).hasLeft());
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertTrue(currentGame.hasEnded());
        assertWonTheGame(playerB);
        assertLostTheGame(playerA);
    }

    @Test
    public void testConcedeDuringCombat() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears", 1);

        attack(1, playerA, "Grizzly Bears");
        concede(1, PhaseStep.DECLARE_BLOCKERS, playerA);

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertTrue("combat concession must take effect", currentGame.hasEnded());
        assertWonTheGame(playerB);
        assertLostTheGame(playerA);
    }

    @Test
    public void testDuplicateConcedeSingleCleanup() {
        runCode("same actor concedes twice before queue processing", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> {
                    UUID actor = player.getId();
                    game.setConcedingPlayer(actor);
                    game.setConcedingPlayer(actor); // duplicate queue request: deduped
                    game.concede(actor); // same actor through the other seam
                    ((GameImpl) game).checkConcede();
                    ((GameImpl) game).checkConcede(); // second drain: no-op

                    Assert.assertTrue(game.getPlayer(actor).hasLeft());
                    Assert.assertTrue(game.hasEnded());
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        assertWonTheGame(playerB);
        assertLostTheGame(playerA);
    }

    @Test
    public void testStaleLostLeftUnknownAndWinnerBoundary() {
        runCode("stale and unknown concession requests fail closed", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> {
                    UUID aId = playerA.getId();
                    UUID bId = playerB.getId();

                    game.concede(aId);
                    ((GameImpl) game).checkConcede();
                    Assert.assertTrue(game.hasEnded());
                    Assert.assertTrue(game.getPlayer(bId).hasWon());

                    // stale: winner submits concession after game end
                    game.concede(bId);
                    ((GameImpl) game).checkConcede();
                    Assert.assertTrue("winner must stay winner after stale concede",
                            game.getPlayer(bId).hasWon());
                    Assert.assertFalse("stale concede must not mark winner lost",
                            game.getPlayer(bId).hasLost());

                    // stale: already-left actor again
                    game.concede(aId);
                    ((GameImpl) game).checkConcede();
                    Assert.assertTrue(game.getPlayer(aId).hasLeft());

                    // unknown actor from nowhere
                    game.concede(UUID.randomUUID());
                    ((GameImpl) game).checkConcede();

                    Assert.assertTrue(game.getPlayer(bId).hasWon());
                    Assert.assertFalse(game.getPlayer(bId).hasLost());
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        assertWonTheGame(playerB);
        assertLostTheGame(playerA);
    }

    @Test
    public void testControlledPlayerCanConcedeSelf() {
        runCode("controlled player concedes themself (CR 723.6)", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> {
                    UUID aId = playerA.getId();
                    UUID bId = playerB.getId();
                    Player controlled = game.getPlayer(bId);
                    // native engine control state (what Mindslaver-class effects establish
                    // for a human-controlled turn; direct setup avoids the AI-control gate,
                    // which is a product limitation, not Rules authority)
                    controlled.setTurnControlledBy(aId);
                    controlled.setGameUnderYourControl(game, false);
                    Assert.assertEquals(aId, controlled.getTurnControlledBy());

                    // the actual player concedes themself: actor is B
                    game.concede(bId);
                    ((GameImpl) game).checkConcede();

                    Assert.assertTrue("controlled player must be able to concede themself",
                            game.getPlayer(bId).hasLeft());
                    Assert.assertFalse(game.getPlayer(aId).hasLeft());
                    Assert.assertFalse(game.getPlayer(aId).hasLost());
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        assertWonTheGame(playerA);
        assertLostTheGame(playerB);
    }

    @Test
    public void testTurnControllerConcedeRemovesOnlySelf() {
        runCode("controller conceding removes exactly the controller (no substitution)", 1,
                PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
                    UUID aId = playerA.getId();
                    UUID bId = playerB.getId();
                    Player controlled = game.getPlayer(bId);
                    controlled.setTurnControlledBy(aId);
                    controlled.setGameUnderYourControl(game, false);
                    Assert.assertEquals(aId, controlled.getTurnControlledBy());

                    // controller concedes: actor is A, exactly A must leave
                    game.concede(aId);
                    ((GameImpl) game).checkConcede();

                    Assert.assertTrue(game.getPlayer(aId).hasLeft());
                    Assert.assertFalse("controlled player must not leave when controller concedes",
                            game.getPlayer(bId).hasLeft());
                    Assert.assertFalse("controlled player must not lose when controller concedes",
                            game.getPlayer(bId).hasLost());
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        assertWonTheGame(playerB);
        assertLostTheGame(playerA);
    }
}
