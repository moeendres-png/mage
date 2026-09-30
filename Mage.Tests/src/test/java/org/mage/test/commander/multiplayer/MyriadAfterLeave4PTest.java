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
 * F-23 (4P Commander): myriad (702.116a) - "for each opponent other than the defending
 * player, you may create a token that's a copy of this creature that's tapped and attacking that
 * player or a planeswalker they control". A player who left the game is no longer an opponent
 * (800.4a), so no token may be offered against them.
 */
public class MyriadAfterLeave4PTest extends CardTestPlayerAPIImpl {

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

    /** Control: A attacks B; A accepts both myriad tokens, which hit C and D. */
    @Test
    public void tokensAttackEachOtherOpponent() {
        addCard(Zone.BATTLEFIELD, playerA, "Warchief Giant");
        attack(1, playerA, "Warchief Giant", playerB);
        setChoice(playerA, true);
        setChoice(playerA, true);
        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();
        assertLife(playerB, 40 - 5);
        assertLife(playerC, 40 - 5);
        assertLife(playerD, 40 - 5);
        assertPermanentCount(playerA, "Warchief Giant", 1);
    }

    /** C left the game before combat: only D may get a token (strict mode fails on an extra ask). */
    @Test
    public void noTokenIsOfferedAgainstAPlayerWhoLeft() {
        addCard(Zone.BATTLEFIELD, playerA, "Warchief Giant");
        concede(1, PhaseStep.PRECOMBAT_MAIN, playerC);
        attack(1, playerA, "Warchief Giant", playerB);
        setChoice(playerA, true);
        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();
        assertLife(playerB, 40 - 5);
        assertLife(playerD, 40 - 5);
        assertPermanentCount(playerA, "Warchief Giant", 1);
    }
}
