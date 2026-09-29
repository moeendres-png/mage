package org.mage.test.multiplayer.apnap;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.FreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.players.Player;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * F-20: the engine's APNAP enumeration primitive (rule 101.4), five players, range of influence ALL.
 * Players are created A..E; turn order is A, E, D, C, B (the engine seats counterclockwise, as the
 * turn sequence of this test proves). Covers: the active player at several seats, a non-active
 * reference player, reversed turn order, a player who left the game, and the unchanged
 * getOpponents contract.
 */
public class ApnapOrderPrimitiveTest extends CardTestPlayerAPIImpl {

    private TestPlayer playerE;

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new FreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 20, 7);
        playerA = createPlayer(game, "PlayerA");
        playerB = createPlayer(game, "PlayerB");
        playerC = createPlayer(game, "PlayerC");
        playerD = createPlayer(game, "PlayerD");
        playerE = createPlayer(game, "PlayerE");
        return game;
    }

    private static List<String> names(Game game, List<UUID> ids) {
        return ids.stream().map(id -> game.getPlayer(id).getName()).collect(Collectors.toList());
    }

    private void expectApnap(int turn, TestPlayer active, String... expected) {
        runCode("apnap turn " + turn, turn, PhaseStep.PRECOMBAT_MAIN, active, (info, player, game) -> {
            Assert.assertEquals(active.getId(), game.getActivePlayerId());
            Assert.assertEquals(info, Arrays.asList(expected), names(game, game.getPlayerIdsInApnapOrder()));
        });
    }

    @Test
    public void startsAtTheActivePlayerAtEverySeat() {
        expectApnap(1, playerA, "PlayerA", "PlayerE", "PlayerD", "PlayerC", "PlayerB");
        expectApnap(2, playerE, "PlayerE", "PlayerD", "PlayerC", "PlayerB", "PlayerA");
        expectApnap(3, playerD, "PlayerD", "PlayerC", "PlayerB", "PlayerA", "PlayerE");
        expectApnap(4, playerC, "PlayerC", "PlayerB", "PlayerA", "PlayerE", "PlayerD");
        setStopAt(4, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void opponentsOfANonActivePlayerStartAtTheActivePlayer() {
        runCode("opponents of C on E's turn", 2, PhaseStep.PRECOMBAT_MAIN, playerE, (info, player, game) -> {
            Assert.assertEquals(Arrays.asList("PlayerE", "PlayerD", "PlayerB", "PlayerA"),
                    names(game, game.getOpponentsInApnapOrder(playerC.getId())));
        });
        setStopAt(2, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void reversedTurnOrderIsHonoured() {
        runCode("reversed", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            game.getState().setReverseTurnOrder(true);
            try {
                Assert.assertTrue(game.isTurnOrderReversed());
                Assert.assertEquals(Arrays.asList("PlayerA", "PlayerB", "PlayerC", "PlayerD", "PlayerE"),
                        names(game, game.getPlayerIdsInApnapOrder()));
            } finally {
                game.getState().setReverseTurnOrder(false);
            }
        });
        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void playersWhoLeftAreSkipped() {
        concede(1, PhaseStep.PRECOMBAT_MAIN, playerD);
        runCode("after D left", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, (info, player, game) -> {
            Assert.assertFalse(game.getPlayer(playerD.getId()).isInGame());
            Assert.assertEquals(Arrays.asList("PlayerA", "PlayerE", "PlayerC", "PlayerB"),
                    names(game, game.getPlayerIdsInApnapOrder()));
            Assert.assertEquals(Arrays.asList("PlayerA", "PlayerE", "PlayerB"),
                    names(game, game.getOpponentsInApnapOrder(playerC.getId())));
        });
        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void getOpponentsKeepsItsDocumentedStartingTurnOrderContract() {
        // Regression: getOpponents is unchanged. It lists the opponents in range by iterating the game's
        // turn-order list (from that list's own pointer), exactly as before this change.
        runCode("getOpponents contract", 2, PhaseStep.PRECOMBAT_MAIN, playerE, (info, player, game) -> {
            for (UUID playerId : game.getPlayerList()) {
                Player reference = game.getPlayer(playerId);
                List<UUID> expected = new ArrayList<>();
                for (UUID id : game.getPlayerList()) {
                    if (!id.equals(playerId) && reference.hasPlayerInRange(id)) {
                        expected.add(id);
                    }
                }
                Assert.assertEquals(names(game, expected), names(game, new ArrayList<>(game.getOpponents(playerId))));
            }
        });
        setStopAt(2, PhaseStep.END_TURN);
        execute();
    }
}
