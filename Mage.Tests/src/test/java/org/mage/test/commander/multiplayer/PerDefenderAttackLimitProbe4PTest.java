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
 * Discovery probe (4P Commander, live pin): Crawlspace ("No more than two creatures can attack
 * you each combat.") controlled by B limits attacks on B only.
 */
public class PerDefenderAttackLimitProbe4PTest extends CardTestPlayerAPIImpl {

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

    private void board() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Raging Goblin");
        addCard(Zone.BATTLEFIELD, playerA, "Runeclaw Bear");
        addCard(Zone.BATTLEFIELD, playerB, "Crawlspace");
    }

    /** Two attack B and one attacks C: all three attack. */
    @Test
    public void twoOnTheLimitedPlayerAndOneElsewhere() {
        board();
        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Runeclaw Bear", playerB);
        attack(1, playerA, "Raging Goblin", playerC);
        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();
        assertLife(playerB, 40 - 4);
        assertLife(playerC, 40 - 1);
    }

    /** Three attack C (not limited): all three attack. */
    @Test
    public void limitDoesNotApplyToAnotherPlayer() {
        board();
        attack(1, playerA, "Grizzly Bears", playerC);
        attack(1, playerA, "Runeclaw Bear", playerC);
        attack(1, playerA, "Raging Goblin", playerC);
        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();
        assertLife(playerC, 40 - 5);
    }

    /** Three try to attack B: at most two do. */
    @Test
    public void atMostTwoAttackTheLimitedPlayer() {
        board();
        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Runeclaw Bear", playerB);
        attack(1, playerA, "Raging Goblin", playerB);
        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(false);
        execute();
        org.junit.Assert.assertTrue("at most two creatures dealt damage to B: life " + playerB.getLife(),
                playerB.getLife() >= 40 - 4);
    }
}
