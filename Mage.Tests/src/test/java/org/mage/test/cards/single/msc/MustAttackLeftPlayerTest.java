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
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * A creature that must attack a player who has left the game has no requirement; that must not
 * cancel the other creatures' requirements. Before the fix, Combat.checkAttackRequirements
 * returned from the whole method on the first such creature, so a goaded creature of the same
 * player escaped its goad.
 *
 * @author commander-lab
 */
public class MustAttackLeftPlayerTest extends CardTestPlayerAPIImpl {

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
    public void testGoadStillAppliesWhenAnotherCreaturesDefenderLeft() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Silver Surfer, Galactus's Herald");
        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.HAND, playerA, "Kang Dynasty");
        addCard(Zone.BATTLEFIELD, playerC, "Grizzly Bears"); // will be forced to attack PlayerB
        addCard(Zone.BATTLEFIELD, playerC, "Hill Giant"); // will be goaded by PlayerA

        // Kang Dynasty chapter I: tap and goad Hill Giant (the other opponents have no creature)
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Kang Dynasty");
        addTarget(playerA, TestPlayer.TARGET_SKIP); // PlayerB
        addTarget(playerA, "Hill Giant"); // PlayerC
        addTarget(playerA, TestPlayer.TARGET_SKIP); // PlayerD
        // Silver Surfer hits PlayerB: Grizzly Bears must attack PlayerB
        attack(1, playerA, "Silver Surfer, Galactus's Herald", playerB);
        addTarget(playerA, "Grizzly Bears");
        // PlayerB leaves the game before PlayerC's turn
        runCode("PlayerB loses", 1, PhaseStep.POSTCOMBAT_MAIN, playerA,
                (info, player, game) -> playerB.lost(game));

        // turn 3 (PlayerC): Bears have no requirement left; Hill Giant is goaded by PlayerA and
        // must attack PlayerD, the only player other than its goader
        setStopAt(3, PhaseStep.END_TURN);
        execute();

        assertLife(playerD, 20 - 3);
        assertLife(playerA, 20);
    }
}
