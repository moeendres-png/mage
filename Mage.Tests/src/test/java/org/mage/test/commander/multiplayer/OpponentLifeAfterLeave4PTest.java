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
 * F-23 regression (4P Commander): "if an opponent has more life than you" right after the only
 * opponent with more life left the game in the same turn (Beza, the Bounding Spring).
 */
public class OpponentLifeAfterLeave4PTest extends CardTestPlayerAPIImpl {

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

    private void castBeza() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.HAND, playerA, "Beza, the Bounding Spring");
        setLife(playerC, 60);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Beza, the Bounding Spring");
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
    }

    /** Control: C (60) has more life than A (40): A gains 4. */
    @Test
    public void controlOpponentWithMoreLife() {
        castBeza();
        execute();
        assertLife(playerA, 44);
    }

    /** C left the game before Beza: no opponent has more life than A. */
    @Test
    public void opponentWhoLeftIsNotCompared() {
        concede(1, PhaseStep.UPKEEP, playerC);
        castBeza();
        execute();
        assertLife(playerA, 40);
    }
}
