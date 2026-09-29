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
 * Discovery probe (4P Commander, turn order A -> D -> C -> B): B's commander is controlled by A
 * (Control Magic) when it dies. Its owner B, not its controller A, chooses whether it goes to the
 * command zone (903.9a).
 */
public class StolenCommanderDiesProbe4PTest extends CardTestPlayerAPIImpl {

    private static final String ISAMARU = "Isamaru, Hound of Konda";

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
    public void ownerChoosesCommandZoneForItsStolenCommander() {
        addCard(Zone.COMMAND, playerB, ISAMARU, 1);
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.HAND, playerA, "Control Magic");
        addCard(Zone.BATTLEFIELD, playerC, "Mountain", 1);
        addCard(Zone.HAND, playerC, "Lightning Bolt");
        castSpell(4, PhaseStep.PRECOMBAT_MAIN, playerB, ISAMARU);
        castSpell(5, PhaseStep.PRECOMBAT_MAIN, playerA, "Control Magic", ISAMARU);
        waitStackResolved(5, PhaseStep.PRECOMBAT_MAIN);
        castSpell(5, PhaseStep.POSTCOMBAT_MAIN, playerC, "Lightning Bolt", ISAMARU);
        setChoice(playerB, true); // owner: move to command zone
        setStopAt(5, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();

        assertCommandZoneCount(playerB, ISAMARU, 1);
        assertGraveyardCount(playerB, ISAMARU, 0);
    }
}
