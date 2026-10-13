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
 * Chapter I in a four-player game: one target per opponent, and every chosen creature is tapped
 * (with a single shared target pointer only the first opponent's creature was).
 *
 * @author commander-lab
 */
public class KangDynastyMultiplayerTest extends CardTestPlayerAPIImpl {

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new FreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 20, 7);
        playerA = createPlayer(game, "PlayerA");
        playerB = createPlayer(game, "PlayerB");
        playerC = createPlayer(game, "PlayerC");
        playerD = createPlayer(game, "PlayerD");
        return game;
    }

    @Test
    public void testEachOpponentsCreatureIsTapped() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Kang Dynasty");
        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerC, "Hill Giant");
        addCard(Zone.BATTLEFIELD, playerD, "Silvercoat Lion");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Kang Dynasty");
        addTarget(playerA, "Grizzly Bears");
        addTarget(playerA, "Hill Giant");
        addTarget(playerA, "Silvercoat Lion");

        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertTapped("Grizzly Bears", true);
        assertTapped("Hill Giant", true);
        assertTapped("Silvercoat Lion", true);
    }

    @Test
    public void testOpponentWithoutCreatureIsSkipped() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, "Kang Dynasty");
        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.BATTLEFIELD, playerC, "Hill Giant");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Kang Dynasty");
        // one target per opponent, in opponent order (B, C, D): only PlayerC has a creature
        addTarget(playerA, TestPlayer.TARGET_SKIP);
        addTarget(playerA, "Hill Giant");
        addTarget(playerA, TestPlayer.TARGET_SKIP);

        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertTapped("Hill Giant", true);
    }
}
