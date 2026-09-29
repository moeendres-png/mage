package org.mage.test.commander.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * Discovery probe (4P Commander, turn order A -> D -> C -> B): D goads A's creature (Disrupt
 * Decorum, "until your next turn") and then leaves the game. 800.4k: the effect lasts until D's
 * next turn would have begun, so on A's following turn (turn 5, before D's would-be turn 6) the
 * creature still must attack, and it must attack a player other than D (D is gone anyway).
 */
public class GoadAfterGoaderLeavesProbe4PTest extends CardTestPlayerAPIImpl {

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

    private void goadThenLeave() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerD, "Mountain", 5);
        addCard(Zone.HAND, playerD, "Disrupt Decorum");
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerD, "Disrupt Decorum");
        waitStackResolved(2, PhaseStep.PRECOMBAT_MAIN);
        concede(2, PhaseStep.POSTCOMBAT_MAIN, playerD);
    }

    /** Turn 5 (A's): still goaded, so the Bears attack B or C although A declares nothing. */
    @Test
    public void goadStillAppliesUntilTheGoadersNextTurnWouldHaveBegun() {
        goadThenLeave();
        setStopAt(5, PhaseStep.END_COMBAT);
        setStrictChooseMode(false);
        execute();
        Assert.assertEquals("the goaded Bears attacked B or C", 40 + 40 - 2,
                playerB.getLife() + playerC.getLife());
    }

    /** Turn 9 (A's next): the goad has ended; A declares no attack and nobody takes damage. */
    @Test
    public void goadEndedLater() {
        goadThenLeave();
        setStopAt(9, PhaseStep.END_COMBAT);
        setStrictChooseMode(false);
        execute();
        Assert.assertEquals("attacked once only (turn 5)", 40 + 40 - 2,
                playerB.getLife() + playerC.getLife());
    }
}
