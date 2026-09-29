package org.mage.test.commander.multiplayer;

import mage.abilities.Ability;
import mage.cards.Card;
import mage.constants.CommanderCardType;
import mage.constants.MultiplayerAttackOption;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.players.Player;
import org.junit.Assert;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * F-18 (Commander Simulator Next): simultaneous Commander-zone choices.
 * <p>
 * CR 903.9a / 704.6d: if a commander is in a graveyard or in exile and was put
 * there since the last time state-based actions were checked, its owner may put
 * it into the command zone. State-based actions are performed simultaneously,
 * and when several players make choices at the same time they do so in APNAP
 * order (CR 101.4). So every owner chooses, starting with the active player and
 * proceeding in turn order, and no commander is moved before all of those
 * choices are made.
 * <p>
 * Every choice is recorded by the owner's player object together with the
 * command-zone contents at that moment. Turn order is not computed from the
 * engine's player list: each commander is cast on its owner's turn in the
 * scheduled order, and a failed cast would break the test, so the observed
 * turn order is what the APNAP expectation is derived from.
 */
public abstract class CommanderZoneApnapTestBase extends CardTestPlayerAPIImpl {

    protected static final String ISAMARU = "Isamaru, Hound of Konda";
    protected static final String ROGRAKH = "Rograkh, Son of Rohgahh";
    protected static final String ARDENN = "Ardenn, Intrepid Archaeologist";
    protected static final String WRATH = "Wrath of God";
    protected static final String FINAL_JUDGMENT = "Final Judgment";
    protected static final List<String> CAMPAIGN_COMMANDERS = java.util.Arrays.asList(ISAMARU, ROGRAKH, ARDENN);

    /** Recorded Commander-zone asks: "owner:commander". */
    protected final List<String> asks = new ArrayList<>();
    /** Commanders already in a command zone at the moment of any ask (must stay empty). */
    protected final List<String> movedBeforeAllChose = new ArrayList<>();
    /** Answer per "Owner:Commander": true = move to command zone. */
    protected final Map<String, Boolean> answers = new HashMap<>();
    protected final List<TestPlayer> seats = new ArrayList<>();

    protected abstract int playerCount();

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new CommanderFreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 40, 7);
        seats.clear();
        for (int index = 0; index < playerCount(); index++) {
            TestPlayer player = createPlayer(game, "Player" + (char) ('A' + index), "CommanderDuel.dck");
            seats.add(player);
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

    /** Scheduled turn order: A first, then the seats in reverse creation order (A, N, ..., B). */
    protected List<TestPlayer> turnOrder() {
        List<TestPlayer> order = new ArrayList<>();
        order.add(seats.get(0));
        for (int index = seats.size() - 1; index >= 1; index--) {
            order.add(seats.get(index));
        }
        return order;
    }

    /** Owners who cast a commander, each on its own turn in turn order. */
    protected void castCommandersOnOwnTurns(Map<TestPlayer, List<String>> commanders) {
        List<TestPlayer> order = turnOrder();
        for (int turn = 1; turn <= order.size(); turn++) {
            TestPlayer owner = order.get(turn - 1);
            for (String commander : commanders.getOrDefault(owner, new ArrayList<>())) {
                castSpell(turn, PhaseStep.PRECOMBAT_MAIN, owner, commander);
                waitStackResolved(turn, PhaseStep.PRECOMBAT_MAIN, owner);
            }
        }
    }

    /** Names of this campaign's commanders currently in any command zone. */
    protected List<String> campaignCommandersInCommandZone(Game game) {
        List<String> found = new ArrayList<>();
        for (Player player : game.getPlayers().values()) {
            for (Card card : game.getCommanderCardsFromCommandZone(player,
                    CommanderCardType.COMMANDER_OR_OATHBREAKER)) {
                if (CAMPAIGN_COMMANDERS.contains(card.getName())) {
                    found.add(player.getName() + ":" + card.getName());
                }
            }
        }
        return found;
    }

    protected void assertCommanderOnBattlefieldAfterOwnTurn(TestPlayer owner, String commander) {
        assertPermanentCount(owner, commander, 1);
    }

    protected static List<String> namesOf(List<TestPlayer> players) {
        List<String> names = new ArrayList<>();
        players.forEach(player -> names.add(player.getName()));
        return names;
    }

    protected void assertAskOrder(List<String> expectedOwners) {
        List<String> owners = new ArrayList<>();
        for (String ask : asks) {
            String owner = ask.substring(0, ask.indexOf(':'));
            if (owners.isEmpty() || !owners.get(owners.size() - 1).equals(owner)) {
                owners.add(owner);
            }
        }
        Assert.assertEquals("CR 101.4: owners choose in APNAP order; asks=" + asks,
                expectedOwners, owners);
        Assert.assertEquals("no commander was moved before every owner chose: "
                + movedBeforeAllChose, new ArrayList<String>(), movedBeforeAllChose);
    }

    // ------------------------------------------------------------ scenarios

    /**
     * Every seat casts a commander; seat B has partners (Rograkh + Ardenn).
     * Odd seats move Isamaru, even seats leave it; B moves Rograkh and leaves
     * Ardenn. The sweeper is cast by {@code turnOrder().get(casterIndex)}.
     */
    protected void runSweeper(String sweeper, int casterIndex, boolean exilePath) {
        Map<TestPlayer, List<String>> commanders = new HashMap<>();
        for (int index = 0; index < seats.size(); index++) {
            TestPlayer seat = seats.get(index);
            addCard(Zone.BATTLEFIELD, seat, "Plains", 6);
            if (index == 1) {
                addCard(Zone.COMMAND, seat, ROGRAKH, 1);
                addCard(Zone.COMMAND, seat, ARDENN, 1);
                commanders.put(seat, java.util.Arrays.asList(ROGRAKH, ARDENN));
                answers.put(seat.getName() + ":" + ROGRAKH, true);
                answers.put(seat.getName() + ":" + ARDENN, false);
            } else {
                addCard(Zone.COMMAND, seat, ISAMARU, 1);
                commanders.put(seat, java.util.Arrays.asList(ISAMARU));
                answers.put(seat.getName() + ":" + ISAMARU, index % 2 == 0);
            }
        }
        List<TestPlayer> order = turnOrder();
        TestPlayer caster = order.get(casterIndex);
        addCard(Zone.HAND, caster, sweeper, 1);
        castCommandersOnOwnTurns(commanders);
        int sweeperTurn = order.size() + 1 + casterIndex;
        castSpell(sweeperTurn, PhaseStep.PRECOMBAT_MAIN, caster, sweeper);

        setStopAt(sweeperTurn, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        List<TestPlayer> apnap = new ArrayList<>();
        for (int offset = 0; offset < order.size(); offset++) {
            apnap.add(order.get((casterIndex + offset) % order.size()));
        }
        assertAskOrder(namesOf(apnap));
        Assert.assertEquals("one ask per dying commander: " + asks, seats.size() + 1, asks.size());
        for (Map.Entry<TestPlayer, List<String>> entry : commanders.entrySet()) {
            for (String commander : entry.getValue()) {
                boolean moved = answers.get(entry.getKey().getName() + ":" + commander);
                assertPermanentCount(entry.getKey(), commander, 0);
                assertCommandZoneCount(entry.getKey(), commander, moved ? 1 : 0);
                if (exilePath) {
                    assertExileCount(entry.getKey(), commander, moved ? 0 : 1);
                } else {
                    assertGraveyardCount(entry.getKey(), commander, moved ? 0 : 1);
                }
            }
        }
    }

    @org.junit.Test
    public void graveyardChoicesInApnapOrderFromFirstPlayer() {
        runSweeper(WRATH, 0, false);
    }

    @org.junit.Test
    public void exileChoicesInApnapOrderFromAnotherActivePlayer() {
        runSweeper(FINAL_JUDGMENT, 1, true);
    }

    @org.junit.Test
    public void singleOwnerIsAskedOnceAndMoved() {
        for (TestPlayer seat : seats) {
            addCard(Zone.BATTLEFIELD, seat, "Plains", 6);
        }
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);
        addCard(Zone.HAND, playerA, WRATH, 1);
        answers.put(playerA.getName() + ":" + ISAMARU, true);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ISAMARU);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, WRATH);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        Assert.assertEquals(java.util.Arrays.asList(playerA.getName() + ":" + ISAMARU), asks);
        assertCommandZoneCount(playerA, ISAMARU, 1);
        assertGraveyardCount(playerA, ISAMARU, 0);
    }

    /** Test player that records each Commander-zone choice and answers it by commander name. */
    static final class RecordingPlayer extends TestPlayer {

        private final transient CommanderZoneApnapTestBase test;

        RecordingPlayer(TestComputerPlayer computerPlayer, CommanderZoneApnapTestBase test) {
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
            if ("Move to command".equals(trueText) && message != null) {
                for (String commander : CAMPAIGN_COMMANDERS) {
                    Boolean answer = test.answers.get(getName() + ":" + commander);
                    if (message.contains(commander) && answer != null) {
                        test.asks.add(getName() + ":" + commander);
                        test.movedBeforeAllChose.addAll(test.campaignCommandersInCommandZone(game));
                        return answer;
                    }
                }
                Assert.fail("unexpected Commander-zone choice for " + getName() + ": " + message);
            }
            return super.chooseUse(outcome, message, secondMessage, trueText, falseText, source, game);
        }

        @Override
        public RecordingPlayer copy() {
            return new RecordingPlayer(this);
        }
    }
}
