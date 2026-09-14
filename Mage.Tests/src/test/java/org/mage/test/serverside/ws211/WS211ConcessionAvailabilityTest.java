package org.mage.test.serverside.ws211;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.GameImpl;
import mage.players.Player;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.util.UUID;

/**
 * WS211 — engine-owned concession availability (Game.canConcede).
 * <p>
 * The Rules Core alone decides whether a specific actor may currently concede.
 * Availability needs no priority, no empty stack and no particular step (CR
 * 104.3a), is unaffected by turn control (CR 723.6), consumes no Rules RNG,
 * and is false for unknown, stale and post-game actors. Availability true is
 * exactly the condition under which Game.concede accepts the request.
 */
public class WS211ConcessionAvailabilityTest extends CardTestPlayerBase {

    @Test
    public void testAvailableForInGamePlayersWithoutPriority() {
        runCode("availability holds for both players on turn 1", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> {
                    Assert.assertTrue(game.canConcede(playerA.getId()));
                    // non-priority player is equally eligible (CR 104.3a "at any time")
                    Assert.assertTrue(game.canConcede(playerB.getId()));
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();
    }

    @Test
    public void testAvailableDuringCombatAndOnOpponentTurn() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears", 1);

        attack(1, playerA, "Grizzly Bears");
        runCode("availability holds mid-combat", 1, PhaseStep.DECLARE_BLOCKERS, playerA,
                (info, player, game) -> {
                    Assert.assertTrue(game.canConcede(playerA.getId()));
                    Assert.assertTrue(game.canConcede(playerB.getId()));
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();
    }

    @Test
    public void testAvailableForControlledPlayerAndController() {
        runCode("turn control does not change availability (CR 723.6)", 1, PhaseStep.PRECOMBAT_MAIN,
                playerA, (info, player, game) -> {
                    UUID aId = playerA.getId();
                    UUID bId = playerB.getId();
                    Player controlled = game.getPlayer(bId);
                    controlled.setTurnControlledBy(aId);
                    controlled.setGameUnderYourControl(game, false);

                    // the controlled player may still concede themself ...
                    Assert.assertTrue(game.canConcede(bId));
                    // ... and so may the controller themself; neither answer
                    // authorizes the controller to concede FOR the controlled player
                    Assert.assertTrue(game.canConcede(aId));
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();
    }

    @Test
    public void testUnavailableForUnknownActor() {
        runCode("unknown actor is never eligible", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> {
                    Assert.assertFalse(game.canConcede(UUID.randomUUID()));
                    Assert.assertFalse(game.canConcede(null));
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();
    }

    @Test
    public void testUnavailableAfterConcedeAndAfterGameOver() {
        runCode("conceder becomes ineligible, survivor stays eligible", 1, PhaseStep.PRECOMBAT_MAIN,
                playerA, (info, player, game) -> {
                    // 4-player style check inside a 2-player game is impossible once the
                    // game ends, so: concede B (non-priority) while the game still runs.
                    Assert.assertTrue(game.canConcede(playerB.getId()));
                    game.concede(playerB.getId());
                    ((GameImpl) game).checkConcede();
                    Assert.assertFalse("conceded player must become ineligible",
                            game.canConcede(playerB.getId()));
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        Assert.assertTrue(currentGame.hasEnded());
        Assert.assertFalse(currentGame.canConcede(playerA.getId()));
        Assert.assertFalse(currentGame.canConcede(playerB.getId()));
        Assert.assertFalse(currentGame.canConcede(UUID.randomUUID()));
    }

    @Test
    public void testAvailabilityEnumerationConsumesNoRulesRng() {
        runCode("canConcede enumeration is RNG-free and state-free", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                (info, player, game) -> {
                    long callsBefore = game.getRulesRandomCalls();
                    int lifeA = game.getPlayer(playerA.getId()).getLife();
                    int lifeB = game.getPlayer(playerB.getId()).getLife();
                    int handA = game.getPlayer(playerA.getId()).getHand().size();

                    for (int i = 0; i < 50; i++) {
                        Assert.assertTrue(game.canConcede(playerA.getId()));
                        Assert.assertTrue(game.canConcede(playerB.getId()));
                        Assert.assertFalse(game.canConcede(UUID.randomUUID()));
                    }

                    Assert.assertEquals("availability enumeration must not consume Rules RNG",
                            callsBefore, game.getRulesRandomCalls());
                    Assert.assertEquals(lifeA, game.getPlayer(playerA.getId()).getLife());
                    Assert.assertEquals(lifeB, game.getPlayer(playerB.getId()).getLife());
                    Assert.assertEquals(handA, game.getPlayer(playerA.getId()).getHand().size());
                    Assert.assertTrue(game.getStack().isEmpty());
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();
    }

    @Test
    public void testAvailabilityMatchesExecutionAcceptance() {
        runCode("canConcede true means concede is accepted; false means ignored", 1,
                PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
                    UUID unknown = UUID.randomUUID();
                    Assert.assertFalse(game.canConcede(unknown));
                    game.concede(unknown); // must be ignored, no corruption
                    ((GameImpl) game).checkConcede();
                    Assert.assertTrue(game.getPlayer(playerA.getId()).isInGame());
                    Assert.assertTrue(game.getPlayer(playerB.getId()).isInGame());
                    Assert.assertFalse(game.hasEnded());

                    Assert.assertTrue(game.canConcede(playerA.getId()));
                    game.concede(playerA.getId());
                    ((GameImpl) game).checkConcede();
                    Assert.assertTrue(game.getPlayer(playerA.getId()).hasLeft());
                });

        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        assertWonTheGame(playerB);
    }
}
