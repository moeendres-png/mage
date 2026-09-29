package org.mage.test.multiplayer.apnap;

import mage.abilities.Ability;
import mage.constants.MultiplayerAttackOption;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.FreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;

/**
 * F-20 (Commander Simulator Next): "each opponent may ..." choices in APNAP order.
 * <p>
 * CR 101.4: when several players make choices at the same time, the active player
 * chooses first, then each other player in turn order. Game.getOpponents iterated the
 * turn-order list from its current pointer (which moves with priority), so opponents
 * could be asked starting from an arbitrary player.
 * <p>
 * Tempt with Discovery (tempting offer) is cast by the active player on the first,
 * second and third turn; every opponent accepts, and a recording player logs who is
 * offered the search, in order. The expected order comes from the scheduled turn order
 * (A first, then seats in reverse creation order), which the casts on those turns prove.
 */
public abstract class EachOpponentApnapTestBase extends CardTestPlayerAPIImpl {

    private static final String TEMPT = "Tempt with Discovery";
    private static final String OFFER = "Search your library for a land card and put it onto the battlefield?";

    protected final List<String> offered = new ArrayList<>();
    protected final List<TestPlayer> seats = new ArrayList<>();

    protected abstract int playerCount();

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new FreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 20, 7);
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

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new RecordingPlayer(new TestComputerPlayer(playerName, rangeOfInfluence), this);
    }

    private List<TestPlayer> turnOrder() {
        List<TestPlayer> order = new ArrayList<>();
        order.add(seats.get(0));
        for (int index = seats.size() - 1; index >= 1; index--) {
            order.add(seats.get(index));
        }
        return order;
    }

    private void castTemptOnTurnOf(int casterIndex) {
        List<TestPlayer> order = turnOrder();
        TestPlayer caster = order.get(casterIndex);
        int turn = casterIndex + 1;
        addCard(Zone.BATTLEFIELD, caster, "Forest", 4);
        addCard(Zone.HAND, caster, TEMPT, 1);
        for (TestPlayer seat : seats) {
            // enough lands for every search (the caster may search 1 + (N - 1) times)
            addCard(Zone.LIBRARY, seat, "Forest", seat == caster ? seats.size() + 1 : 3);
            if (seat != caster) {
                addTarget(seat, "Forest");
            }
        }
        addTarget(caster, "Forest"); // own search
        StringBuilder more = new StringBuilder("Forest"); // then one land per opponent who searched
        for (int count = 1; count < seats.size() - 1; count++) {
            more.append("^Forest");
        }
        addTarget(caster, more.toString());
        castSpell(turn, PhaseStep.PRECOMBAT_MAIN, caster, TEMPT);
        setStopAt(turn, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        List<String> expected = new ArrayList<>();
        for (int offset = 1; offset < order.size(); offset++) {
            expected.add(order.get((casterIndex + offset) % order.size()).getName());
        }
        Assert.assertEquals("CR 101.4: opponents choose in APNAP order from the active caster",
                expected, offered);
        assertPermanentCount(caster, "Forest", 4 + 1 + (seats.size() - 1));
    }

    @Test
    public void firstPlayerInTurnOrderCasts() {
        castTemptOnTurnOf(0);
    }

    @Test
    public void secondPlayerInTurnOrderCasts() {
        castTemptOnTurnOf(1);
    }

    @Test
    public void thirdPlayerInTurnOrderCasts() {
        castTemptOnTurnOf(2);
    }

    static final class RecordingPlayer extends TestPlayer {

        private final transient EachOpponentApnapTestBase test;

        RecordingPlayer(TestComputerPlayer computerPlayer, EachOpponentApnapTestBase test) {
            super(computerPlayer);
            this.test = test;
        }

        private RecordingPlayer(RecordingPlayer player) {
            super(player);
            this.test = player.test;
        }

        @Override
        public boolean chooseUse(Outcome outcome, String message, String secondMessage,
                                 String trueText, String falseText, Ability source, Game game) {
            if (OFFER.equals(message)) {
                test.offered.add(getName());
                return true;
            }
            return super.chooseUse(outcome, message, secondMessage, trueText, falseText, source, game);
        }

        @Override
        public RecordingPlayer copy() {
            return new RecordingPlayer(this);
        }
    }
}
