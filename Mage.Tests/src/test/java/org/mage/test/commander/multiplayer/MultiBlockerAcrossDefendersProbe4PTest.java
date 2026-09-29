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
 * Discovery probe (4P Commander): Palace Guard ("can block any number of creatures") controlled
 * by B may block only creatures attacking B (802.4a), not A's creature attacking C.
 */
public class MultiBlockerAcrossDefendersProbe4PTest extends CardTestPlayerAPIImpl {

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

    /** Control: B's Palace Guard blocks both attackers aimed at B. */
    @Test
    public void blocksEveryAttackerAttackingItsController() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Raging Goblin");
        addCard(Zone.BATTLEFIELD, playerB, "Palace Guard");
        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Raging Goblin", playerB);
        block(1, playerB, "Palace Guard", "Grizzly Bears");
        block(1, playerB, "Palace Guard", "Raging Goblin");
        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(false); // Palace Guard's damage assignment among two blocked creatures
        execute();
        assertLife(playerB, 40);
    }

    /** Palace Guard can't also block the creature attacking C. */
    @Test
    public void cantBlockACreatureAttackingAnotherPlayer() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Raging Goblin");
        addCard(Zone.BATTLEFIELD, playerB, "Palace Guard");
        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Raging Goblin", playerC);
        block(1, playerB, "Palace Guard", "Grizzly Bears");
        block(1, playerB, "Palace Guard", "Raging Goblin");
        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(false);
        execute();
        assertLife(playerB, 40);
        assertLife(playerC, 40 - 1);
    }
}
