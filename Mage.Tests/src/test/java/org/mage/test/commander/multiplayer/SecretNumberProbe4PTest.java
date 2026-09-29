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
 * Discovery probe (4P Commander): Menacing Ogre - each player secretly chooses a number; each player
 * with the highest number loses that much life; if the controller is one of them, two +1/+1 counters.
 */
public class SecretNumberProbe4PTest extends CardTestPlayerAPIImpl {

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
    public void everyPlayerChoosesAndTheHighestLoseLife() {
        addCard(Zone.HAND, playerA, "Menacing Ogre");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 5);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Menacing Ogre");
        setChoiceAmount(playerA, 3);
        setChoiceAmount(playerB, 7);
        setChoiceAmount(playerC, 7);
        setChoiceAmount(playerD, 1);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();
        assertLife(playerA, 40);
        assertLife(playerB, 40 - 7);
        assertLife(playerC, 40 - 7);
        assertLife(playerD, 40);
        assertPowerToughness(playerA, "Menacing Ogre", 3, 3);
    }
}
