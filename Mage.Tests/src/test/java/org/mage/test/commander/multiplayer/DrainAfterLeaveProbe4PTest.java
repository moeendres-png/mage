package org.mage.test.commander.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import org.junit.Test;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * Discovery probe (4P Commander, live pin): Exsanguinate ("Each opponent loses X life. You gain
 * life equal to the life lost this way.") after an opponent left the game this turn.
 */
public class DrainAfterLeaveProbe4PTest extends CardTestPlayerAPIImpl {

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

    private void exsanguinateX3() {
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 5);
        addCard(Zone.HAND, playerA, "Exsanguinate");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Exsanguinate");
        setChoice(playerA, "X=3");
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
    }

    /** Control: three opponents lose 3 each, A gains 9. */
    @Test
    public void controlThreeOpponents() {
        exsanguinateX3();
        execute();
        assertLife(playerA, 49);
    }

    /** C conceded earlier this turn: only B and D lose life, A gains 6. */
    @Test
    public void opponentWhoLeftDoesNotLoseLifeForYou() {
        concede(1, PhaseStep.UPKEEP, playerC);
        exsanguinateX3();
        execute();
        assertLife(playerB, 37);
        assertLife(playerD, 37);
        assertLife(playerA, 46);
    }
}
