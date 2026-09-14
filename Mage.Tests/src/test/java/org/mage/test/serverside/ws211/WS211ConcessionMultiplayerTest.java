package org.mage.test.serverside.ws211;

import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.GameImpl;
import mage.game.stack.Spell;
import mage.players.Player;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestMultiPlayerBaseWithRangeAll;

import java.util.UUID;

/**
 * WS211 — authoritative concession in 4-player games (primary project mode).
 *
 * A concession must eliminate only the conceding player; the remaining three
 * continue under native engine leave/end semantics (CR 800.4 family).
 */
public class WS211ConcessionMultiplayerTest extends CardTestMultiPlayerBaseWithRangeAll {

    @Test
    public void testFourPlayerConcedeContinuesWithThree() {
        // Player order: A -> D -> C -> B. B concedes on turn 2 without priority.
        concede(2, PhaseStep.POSTCOMBAT_MAIN, playerB);

        checkPlayerInGame("B out after concede", 2, PhaseStep.END_TURN, playerD, playerB, false);
        checkPlayerInGame("A continues", 3, PhaseStep.PRECOMBAT_MAIN, playerD, playerA, true);
        checkPlayerInGame("C continues", 3, PhaseStep.PRECOMBAT_MAIN, playerD, playerC, true);
        checkPlayerInGame("D continues", 3, PhaseStep.PRECOMBAT_MAIN, playerD, playerD, true);
        checkPlayerInGame("B still out", 3, PhaseStep.PRECOMBAT_MAIN, playerD, playerB, false);

        setStopAt(4, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertFalse("three remaining players must continue; game must not end",
                currentGame.hasEnded());
        assertHasNotLostTheGame(playerA);
        assertHasNotLostTheGame(playerC);
        assertHasNotLostTheGame(playerD);
        assertLostTheGame(playerB);
    }

    @Test
    public void testFourPlayerControlledSelfConcede() {
        runCode("controlled player concedes themself in 4-player (CR 723.6)", 1, PhaseStep.PRECOMBAT_MAIN,
                playerA, (info, player, game) -> {
                    UUID aId = playerA.getId();
                    UUID dId = playerD.getId();
                    Player controlled = game.getPlayer(dId);
                    controlled.setTurnControlledBy(aId);
                    controlled.setGameUnderYourControl(game, false);
                    Assert.assertEquals(aId, controlled.getTurnControlledBy());

                    game.concede(dId);
                    ((GameImpl) game).checkConcede();

                    Assert.assertTrue(game.getPlayer(dId).hasLeft());
                    Assert.assertTrue(game.getPlayer(aId).isInGame());
                    Assert.assertTrue(game.getPlayer(playerB.getId()).isInGame());
                    Assert.assertTrue(game.getPlayer(playerC.getId()).isInGame());
                    Assert.assertFalse(game.hasEnded());
                });

        checkPlayerInGame("D still out", 2, PhaseStep.PRECOMBAT_MAIN, playerA, playerD, false);
        checkPlayerInGame("game continues", 2, PhaseStep.PRECOMBAT_MAIN, playerA, playerA, true);

        setStopAt(3, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertFalse(currentGame.hasEnded());
        assertLostTheGame(playerD);
    }

    @Test
    public void testFourPlayerControllerConcedeRemovesOnlySelf() {
        runCode("controller conceding removes exactly the controller in 4-player", 1,
                PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
                    UUID aId = playerA.getId();
                    UUID bId = playerB.getId();
                    Player controlled = game.getPlayer(bId);
                    controlled.setTurnControlledBy(aId);
                    controlled.setGameUnderYourControl(game, false);

                    game.concede(aId);
                    ((GameImpl) game).checkConcede();

                    Assert.assertTrue(game.getPlayer(aId).hasLeft());
                    Assert.assertTrue("controlled player must remain",
                            game.getPlayer(bId).isInGame());
                    Assert.assertTrue(game.getPlayer(playerC.getId()).isInGame());
                    Assert.assertTrue(game.getPlayer(playerD.getId()).isInGame());
                    Assert.assertFalse(game.hasEnded());
                });

        checkPlayerInGame("B still in", 2, PhaseStep.PRECOMBAT_MAIN, playerB, playerB, true);
        checkPlayerInGame("C still in", 2, PhaseStep.PRECOMBAT_MAIN, playerB, playerC, true);
        checkPlayerInGame("D still in", 2, PhaseStep.PRECOMBAT_MAIN, playerB, playerD, true);
        checkPlayerInGame("A still out", 2, PhaseStep.PRECOMBAT_MAIN, playerB, playerA, false);

        setStopAt(3, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertFalse(currentGame.hasEnded());
        assertLostTheGame(playerA);
    }

    @Test
    public void testFourPlayerDuplicateAndStaleRequests() {        runCode("duplicate and stale requests do not corrupt 4-player game", 1, PhaseStep.PRECOMBAT_MAIN,
                playerA, (info, player, game) -> {
                    UUID cId = playerC.getId();
                    game.setConcedingPlayer(cId);
                    game.setConcedingPlayer(cId); // duplicate: deduped
                    game.concede(cId);
                    ((GameImpl) game).checkConcede();
                    ((GameImpl) game).checkConcede(); // second drain: no-op
                    Assert.assertTrue(game.getPlayer(cId).hasLeft());

                    // stale: already-left actor again + unknown actor
                    game.concede(cId);
                    game.concede(UUID.randomUUID());
                    ((GameImpl) game).checkConcede();

                    Assert.assertTrue(game.getPlayer(playerA.getId()).isInGame());
                    Assert.assertTrue(game.getPlayer(playerB.getId()).isInGame());
                    Assert.assertTrue(game.getPlayer(playerD.getId()).isInGame());
                    Assert.assertFalse(game.hasEnded());
                });

        checkPlayerInGame("C still out", 2, PhaseStep.PRECOMBAT_MAIN, playerA, playerC, false);

        setStopAt(3, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertFalse(currentGame.hasEnded());
        assertLostTheGame(playerC);
    }

    @Test
    public void testFourPlayerConcedeClearsLeaversStackObjects() {
        addCard(Zone.HAND, playerC, "Lightning Bolt", 1);

        runCode("concede with nonempty stack while game continues", 1, PhaseStep.PRECOMBAT_MAIN,
                playerA, (info, player, game) -> {
                    UUID cId = playerC.getId();
                    Player leaver = game.getPlayer(cId);
                    Card bolt = null;
                    for (UUID cardId : leaver.getHand()) {
                        Card candidate = game.getCard(cardId);
                        if (candidate != null && "Lightning Bolt".equals(candidate.getName())) {
                            bolt = candidate;
                            break;
                        }
                    }
                    Assert.assertNotNull("test setup: Lightning Bolt must be in hand", bolt);
                    game.getStack().push(game, new Spell(bolt, bolt.getSpellAbility(), cId, Zone.HAND, game));
                    Assert.assertFalse("test setup: stack must be nonempty", game.getStack().isEmpty());

                    game.concede(cId);
                    ((GameImpl) game).checkConcede();

                    Assert.assertTrue("leaver's stack objects must cease to exist",
                            game.getStack().isEmpty());
                    Assert.assertTrue(leaver.hasLeft());
                    Assert.assertFalse(game.hasEnded());
                });

        checkPlayerInGame("C still out", 2, PhaseStep.PRECOMBAT_MAIN, playerA, playerC, false);

        setStopAt(3, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertFalse(currentGame.hasEnded());
        assertLostTheGame(playerC);
    }
}
