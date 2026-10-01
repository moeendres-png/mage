package org.mage.test.commander.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.RangeOfInfluence;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;

import java.io.FileNotFoundException;

/**
 * F-43 five-player mirror. Inherits the attacker, blocker, trample,
 * first-strike and double-strike leave-during-assignment regressions.
 */
public class CombatDamageSourceLeaves5PTest extends CombatDamageSourceLeaves4PTest {

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new CommanderFreeForAll(
                MultiplayerAttackOption.MULTIPLE,
                RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0),
                20,
                7
        );
        playerA = createPlayer(game, "PlayerA");
        playerB = createPlayer(game, "PlayerB");
        playerC = createPlayer(game, "PlayerC");
        playerD = createPlayer(game, "PlayerD");
        createPlayer(game, "PlayerE");
        return game;
    }
}
