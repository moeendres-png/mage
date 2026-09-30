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
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;

/**
 * F-23 (Commander Simulator Next): "the number of opponents you have" right after an opponent
 * left the game in the same turn.
 * <p>
 * A player who left the game is no longer in the game and so is no longer an opponent. The
 * pinned {@code OpponentsCount} counted {@code game.getOpponents(controller)} without excluding
 * players who left, which keeps them until the ranges of influence are recalculated at the next
 * turn, so e.g. Inspired Sphinx ("When this creature enters, draw a card for each opponent you
 * have.") drew for a player who had already conceded.
 * <p>
 * The first player does not skip its first draw in a multiplayer game, so A's hand holds one card
 * before the Sphinx resolves.
 */
public abstract class OpponentsCountAfterLeaveTestBase extends CardTestPlayerAPIImpl {

    protected final List<TestPlayer> seats = new ArrayList<>();

    protected abstract int playerCount();

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new CommanderFreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 40, 7);
        seats.clear();
        for (int index = 0; index < playerCount(); index++) {
            seats.add(createPlayer(game, "Player" + (char) ('A' + index)));
        }
        playerA = seats.get(0);
        playerB = seats.get(1);
        playerC = seats.get(2);
        if (playerCount() > 3) {
            playerD = seats.get(3);
        }
        return game;
    }

    private void castSphinx() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 7);
        addCard(Zone.HAND, playerA, "Inspired Sphinx");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Inspired Sphinx");
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
    }

    @Test
    public void everyOpponentInTheGameIsCounted() {
        castSphinx();
        execute();
        assertHandCount(playerA, 1 + (playerCount() - 1));
    }

    @Test
    public void anOpponentWhoLeftThisTurnIsNotCounted() {
        concede(1, PhaseStep.UPKEEP, playerC);
        castSphinx();
        execute();
        assertHandCount(playerA, 1 + (playerCount() - 2));
    }

    @Test
    public void twoOpponentsWhoLeftThisTurnAreNotCounted() {
        concede(1, PhaseStep.UPKEEP, playerB);
        concede(1, PhaseStep.UPKEEP, playerC);
        castSphinx();
        execute();
        assertHandCount(playerA, 1 + (playerCount() - 3));
    }
}
