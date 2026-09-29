package org.mage.test.multiplayer.apnap;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.game.FreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.HashSet;
import java.util.List;
import java.util.UUID;

/**
 * F-20: getOpponentsInApnapOrder preserves range of influence. Five players, range ONE: every
 * opponent in APNAP order is one getOpponents also lists (same membership), and none outside range.
 */
public class ApnapOrderRangeOfInfluenceTest extends CardTestPlayerAPIImpl {

    private TestPlayer playerE;

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new FreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ONE,
                MulliganType.GAME_DEFAULT.getMulligan(0), 20, 7);
        playerA = createPlayer(game, "PlayerA");
        playerB = createPlayer(game, "PlayerB");
        playerC = createPlayer(game, "PlayerC");
        playerD = createPlayer(game, "PlayerD");
        playerE = createPlayer(game, "PlayerE");
        return game;
    }

    @Test
    public void rangeOfInfluenceIsPreserved() {
        runCode("range one", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            for (UUID playerId : game.getPlayerList()) {
                List<UUID> apnap = game.getOpponentsInApnapOrder(playerId);
                Assert.assertEquals("same opponents as getOpponents for " + game.getPlayer(playerId).getName(),
                        new HashSet<>(game.getOpponents(playerId, true)), new HashSet<>(apnap));
                Assert.assertTrue("range ONE restricts opponents at five players", apnap.size() < 4);
            }
        });
        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }
}
