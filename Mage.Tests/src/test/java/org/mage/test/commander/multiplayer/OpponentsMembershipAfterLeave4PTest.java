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
 * F-23 API contract: the ordinary opponent query exposes only opponents still in the game.
 * The explicit false overload remains available for engine code that deliberately needs the
 * turn-start range snapshot.
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
    public void defaultOpponentQueryExcludesDepartedPlayerButSnapshotOverloadCanRetainIt() {
        concede(1, PhaseStep.UPKEEP, playerC);
        runCode("opponent membership after leave", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Assert.assertFalse("default opponent membership excludes a player who left",
                    game.getOpponents(playerA.getId()).contains(playerC.getId()));
            Assert.assertTrue("explicit snapshot access remains available",
                    game.getOpponents(playerA.getId(), false).contains(playerC.getId()));
            Assert.assertTrue(game.getOpponents(playerA.getId()).contains(playerB.getId()));
            Assert.assertTrue(game.getOpponents(playerA.getId()).contains(playerD.getId()));
        });
        setStopAt(1, PhaseStep.PRECOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();
    }
}
