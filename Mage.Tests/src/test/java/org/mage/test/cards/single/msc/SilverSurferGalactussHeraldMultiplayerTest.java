package org.mage.test.cards.single.msc;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.FreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import org.junit.Test;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * "Whenever Silver Surfer deals combat damage to a player, until the end of your next turn,
 * target creature attacks that player each combat if able." in a four-player game.
 *
 * @author commander-lab
 */
public class SilverSurferGalactussHeraldMultiplayerTest extends CardTestPlayerAPIImpl {

    private static final String SURFER = "Silver Surfer, Galactus's Herald";

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new FreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 20, 7);
        // turn order: A -> D -> C -> B
        playerA = createPlayer(game, "PlayerA");
        playerB = createPlayer(game, "PlayerB");
        playerC = createPlayer(game, "PlayerC");
        playerD = createPlayer(game, "PlayerD");
        return game;
    }

    @Test
    public void testTargetCreatureMustAttackTheDamagedPlayer() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, SURFER);
        addCard(Zone.BATTLEFIELD, playerC, "Grizzly Bears");

        attack(1, playerA, SURFER, playerB);
        addTarget(playerA, "Grizzly Bears");

        // turn 3 is PlayerC's: no attack command, the requirement forces the Bears into PlayerB
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 4 - 2);
        assertLife(playerA, 20);
        assertLife(playerD, 20);
    }

    @Test
    public void testRequirementEndsAfterYourNextTurn() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, SURFER);
        addCard(Zone.BATTLEFIELD, playerC, "Grizzly Bears");

        attack(1, playerA, SURFER, playerB);
        addTarget(playerA, "Grizzly Bears");

        // PlayerA's next turn is turn 5; PlayerC's turn 7 comes after it: no forced attack there.
        // Turn 3 still forces the attack (2 damage); turn 7 must not add another 2.
        setStopAt(7, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 4 - 2);
    }
}
