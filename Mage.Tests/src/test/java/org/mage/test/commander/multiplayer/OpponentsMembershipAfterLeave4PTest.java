package org.mage.test.commander.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * F-23 API contract: current gameplay membership is explicit via getOpponentsInGame.
 * The legacy/default opponent query remains the turn-start range snapshot because trigger/history
 * semantics can intentionally need a player who left during the turn.
 */
public class OpponentsMembershipAfterLeave4PTest extends CardTestPlayerAPIImpl {

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new CommanderFreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 40, 7);
        playerA = createPlayer(game, "PlayerA");
        playerB = createPlayer(game, "PlayerB");
        playerC = createPlayer(game, "PlayerC");
        playerD = createPlayer(game, "PlayerD");
        return game;
    }

    @Test
    public void explicitInGameOpponentQueryExcludesDepartedPlayerWhileSnapshotRetainsIt() {
        concede(1, PhaseStep.UPKEEP, playerC);
        runCode("opponent membership after leave", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Assert.assertFalse("explicit in-game opponent primitive excludes a player who left",
                    game.getOpponentsInGame(playerA.getId()).contains(playerC.getId()));
            Assert.assertTrue("default query retains the turn-start snapshot",
                    game.getOpponents(playerA.getId()).contains(playerC.getId()));
            Assert.assertEquals("default query remains the explicit snapshot overload",
                    game.getOpponents(playerA.getId(), false), game.getOpponents(playerA.getId()));
            Assert.assertTrue(game.getOpponentsInGame(playerA.getId()).contains(playerB.getId()));
            Assert.assertTrue(game.getOpponentsInGame(playerA.getId()).contains(playerD.getId()));
        });
        setStopAt(1, PhaseStep.PRECOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();
    }
}
