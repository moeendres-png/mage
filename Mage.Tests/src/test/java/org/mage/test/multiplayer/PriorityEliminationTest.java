package org.mage.test.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.FreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.TwoPlayerDuel;
import mage.game.mulligan.MulliganType;
import mage.game.stack.Spell;
import mage.game.stack.StackObject;
import mage.players.Player;
import org.junit.Assert;
import org.junit.Before;
import org.junit.Rule;
import org.junit.Test;
import org.junit.rules.TestName;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Priority handling when a state-based action eliminates a player who already holds priority (Lab #507).
 * <p>
 * Rules consulted (official Comprehensive Rules, 2026-09-25 build,
 * https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt,
 * SHA256 8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca):
 * <ul>
 *   <li>117.5 - state-based actions (and then triggered abilities) are performed and repeated
 *       before the player who was about to receive priority actually receives it. So the player
 *       about to act can be removed by those state-based actions.</li>
 *   <li>704.5a - a player whose life total is 0 or less loses the game.</li>
 *   <li>118.3b - paying life as a cost subtracts that life from the payer's life total.</li>
 *   <li>800.4a - when a player leaves, priority they held passes to the next player in turn order
 *       who is still in the game.</li>
 *   <li>800.4j - a player leaving during their own turn does not abort that turn; it completes
 *       without an active player, and priority goes to the next player in turn order.</li>
 *   <li>800.4b - an object that would enter the battlefield under a departed player's control stays
 *       where it is.</li>
 * </ul>
 * <p>
 * Every elimination here is produced by real engine rules only: a life-payment cost (118.3b) drops
 * the payer's life total to 0 and the engine's own 704.5a check removes the player. No win/loss or
 * other outcome is injected and no priority loop is bypassed. The only test-side instrumentation is
 * {@link PriorityRecordingPlayer}, which records every {@link Player#priority(Game)} call the engine
 * makes plus the recorded player's game status at that moment; it never changes engine behaviour.
 * <p>
 * Table size is chosen by a token in the test method name because the shared {@code @Before reset()}
 * of the harness calls {@link #createNewGameAndPlayers()} before the test body runs, so the table
 * must be sized up front. Players are added in the same order as the standard multiplayer bases
 * (A, B, C, D, E). XMage's player list is built in reverse insertion order and the cycle starts at
 * the starting player, so the turn order is A,B / A,C,B / A,D,C,B / A,E,D,C,B for 2/3/4/5 seats.
 * {@link #assertActivePlayer(int, PhaseStep, TestPlayer, TestPlayer)} asserts that at runtime rather
 * than assuming it.
 *
 * @author Foundry Lab #507
 */
public class PriorityEliminationTest extends CardTestPlayerAPIImpl {

    private static final String TWO_PLAYERS = "twoPlayers";
    private static final String THREE_PLAYERS = "threePlayers";
    private static final String FOUR_PLAYERS = "fourPlayers";
    private static final String FIVE_PLAYERS = "fivePlayers";

    /**
     * Shadowcloak Vampire's activated ability. Its only cost is paying life, so no mana is needed.
     */
    private static final String PAY_TWO_LIFE = "Pay 2 life:";

    private static final String SHADOWCLOAK_VAMPIRE = "Shadowcloak Vampire";
    private static final String GRIZZLY_BEARS = "Grizzly Bears";
    private static final String GIANT_GROWTH = "Giant Growth";
    private static final String SILVERCOAT_LION = "Silvercoat Lion";

    /**
     * Every engine-driven priority request as {@code name|Turn|STEP|inGame=<bool>}.
     */
    private static final List<String> PRIORITY_CALLS = new ArrayList<>();

    @Rule
    public TestName testName = new TestName();

    private TestPlayer playerE;

    @Before
    public void clearPriorityRecording() {
        PRIORITY_CALLS.clear();
    }

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new PriorityRecordingPlayer(new TestComputerPlayer(playerName, rangeOfInfluence));
    }

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        int seats = seatsFor(testName.getMethodName());
        if (seats == 2) {
            Game game = new TwoPlayerDuel(MultiplayerAttackOption.LEFT, RangeOfInfluence.ALL,
                    MulliganType.GAME_DEFAULT.getMulligan(0), 20, 7, 60);
            playerA = createPlayer(game, "PlayerA");
            playerB = createPlayer(game, "PlayerB");
            return game;
        }
        Game game = new FreeForAll(MultiplayerAttackOption.LEFT, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 20, 7);
        playerA = createPlayer(game, "PlayerA");
        if (seats >= 2) {
            playerB = createPlayer(game, "PlayerB");
        }
        if (seats >= 3) {
            playerC = createPlayer(game, "PlayerC");
        }
        if (seats >= 4) {
            playerD = createPlayer(game, "PlayerD");
        }
        if (seats >= 5) {
            playerE = createPlayer(game, "PlayerE");
        }
        return game;
    }

    private int seatsFor(String methodName) {
        if (methodName == null) {
            throw new IllegalStateException("test method name is required to size the table");
        }
        if (methodName.contains(TWO_PLAYERS)) {
            return 2;
        }
        if (methodName.contains(THREE_PLAYERS)) {
            return 3;
        }
        if (methodName.contains(FIVE_PLAYERS)) {
            return 5;
        }
        if (methodName.contains(FOUR_PLAYERS)) {
            return 4;
        }
        throw new IllegalStateException("test method name must contain a table size token: " + methodName);
    }

    // ------------------------------------------------------------------------------------------
    // Regression 1: the active player is removed by a state-based action inside the priority window
    // it already entered, so it must not be asked for priority again, and its turn must still run to
    // completion (800.4j) with the next player in turn order taking over.
    // ------------------------------------------------------------------------------------------

    @Test
    public void test_fourPlayers_activePlayerEliminatedDuringOwnPriorityGetsNoPriority() {
        // turn order A, D, C, B
        assertActivePlayer(1, PhaseStep.PRECOMBAT_MAIN, playerA, playerA);
        assertActivePlayer(2, PhaseStep.PRECOMBAT_MAIN, playerA, playerD);
        assertActivePlayer(3, PhaseStep.PRECOMBAT_MAIN, playerA, playerC);
        assertActivePlayer(4, PhaseStep.PRECOMBAT_MAIN, playerA, playerB);

        setupLethalLifePayment(3, playerC);

        // the rest of the departed active player's turn still runs without an active player (800.4j)
        checkStackSize("stack during the rest of the departed active player's turn",
                3, PhaseStep.POSTCOMBAT_MAIN, playerB, 0);

        setStopAt(4, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertSeats("PlayerA, PlayerB, PlayerC, PlayerD", 4);
        assertLost("PlayerC is removed by the 704.5a life total state-based action", playerC);
        assertInGame("PlayerA survives", playerA);
        assertInGame("PlayerB survives", playerB);
        assertInGame("PlayerD survives", playerD);

        // control: the eliminated player did hold priority before the state-based action
        assertReceivedPriority("active player holds priority before elimination", playerC, 3);

        // 117.5 + 800.4a: nobody may be asked for priority after leaving the game
        assertNoPriorityForDepartedPlayer("117.5/800.4a");

        // 800.4a + 800.4j: priority and then the turn itself move to the next player in turn order
        assertReceivedPriority("next player in turn order takes over priority", playerB, 3);
        assertReceivedPriority("surviving players keep getting priority", playerA, 3);
        assertReceivedPriority("surviving players keep getting priority", playerD, 3);
        assertReceivedPriority("next player in turn order starts the following turn", playerB, 4);

        assertTurn(4);
        Assert.assertEquals("turn 4 must be PlayerB's turn (next in turn order after PlayerC)",
                playerB.getId(), currentGame.getActivePlayerId());
    }

    /**
     * Regression 2: the same defect for a player that is not the active player. A surviving player
     * pays lethal life with the priority it already holds and must not be asked for priority again.
     * PlayerC's turn is still skipped and the table keeps running.
     */
    @Test
    public void test_fourPlayers_nonActivePlayerEliminatedDuringPriorityGetsNoPriority() {
        // PlayerA is the active player of turn 1 and every player receives priority in that step
        assertActivePlayer(1, PhaseStep.PRECOMBAT_MAIN, playerA, playerA);
        assertActivePlayer(2, PhaseStep.PRECOMBAT_MAIN, playerA, playerD);

        setLife(playerB, 2);
        addCard(Zone.BATTLEFIELD, playerB, SHADOWCLOAK_VAMPIRE);
        // priority order in turn 1 starts with the active player PlayerA, then PlayerB
        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerB, PAY_TWO_LIFE);

        setStopAt(2, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertSeats("PlayerA, PlayerB, PlayerC, PlayerD", 4);
        assertLost("PlayerB is removed by the 704.5a life total state-based action", playerB);
        assertInGame("PlayerA survives", playerA);
        assertInGame("PlayerC survives", playerC);
        assertInGame("PlayerD survives", playerD);

        assertNoPriorityForDepartedPlayer("117.5/800.4a");
        assertReceivedPriority("surviving players keep getting priority", playerA, 1);
        assertReceivedPriority("surviving players keep getting priority", playerC, 1);

        // PlayerB is gone, so its turn is skipped and PlayerD takes turn 2
        assertTurn(2);
        Assert.assertEquals("turn 2 must be PlayerD's turn (PlayerB is out of the game)",
                playerD.getId(), currentGame.getActivePlayerId());
    }

    /**
     * Regression 3: PlayerC casts a spell and then pays lethal life while that spell is still the
     * only object on the stack, so the spell is owned by a player who leaves the game before it can
     * resolve (800.4a/800.4b). A surviving player then puts a different object of its own on the
     * stack, that object must really resolve, and the step must continue to the next turn.
     */
    @Test
    public void test_fourPlayers_stackOfDepartedActivePlayerIsRemovedAndSurvivorStackObjectResolves() {
        // turn order A, D, C, B
        assertActivePlayer(3, PhaseStep.PRECOMBAT_MAIN, playerA, playerC);
        assertActivePlayer(4, PhaseStep.PRECOMBAT_MAIN, playerA, playerB);

        setLife(playerC, 2);
        addCard(Zone.BATTLEFIELD, playerC, SHADOWCLOAK_VAMPIRE);
        addCard(Zone.HAND, playerC, GRIZZLY_BEARS);
        addCard(Zone.BATTLEFIELD, playerC, "Forest", 2);

        // a surviving player's own stack object, with an observable resolution
        addCard(Zone.BATTLEFIELD, playerB, SILVERCOAT_LION);
        addCard(Zone.HAND, playerB, GIANT_GROWTH);
        addCard(Zone.BATTLEFIELD, playerB, "Forest", 1);

        // PlayerC keeps priority until it passes, so its own windows prove the spell is pending
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerC, GRIZZLY_BEARS);
        checkStackSize("departed player's spell is pending on the stack",
                3, PhaseStep.PRECOMBAT_MAIN, playerC, 1);
        checkStackObject("departed player's spell is the pending object",
                3, PhaseStep.PRECOMBAT_MAIN, playerC, "Cast " + GRIZZLY_BEARS, 1);
        // PlayerC pays lethal life while its own spell is still on the stack
        activateAbility(3, PhaseStep.PRECOMBAT_MAIN, playerC, PAY_TWO_LIFE);

        // after the elimination PlayerB puts a different object of its own on the stack
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerB, GIANT_GROWTH, SILVERCOAT_LION);

        // the surviving player's object really resolves and nothing of the departed player is left
        checkPT("survivor's own stack object resolved",
                3, PhaseStep.POSTCOMBAT_MAIN, playerB, SILVERCOAT_LION, 5, 5);
        checkStackSize("stack is empty again at the end of the departed active player's turn",
                3, PhaseStep.POSTCOMBAT_MAIN, playerA, 0);
        runCode("no object of the departed player is left in the game",
                3, PhaseStep.POSTCOMBAT_MAIN, playerA, (info, player, game) -> {
                    List<StackObject> leftOver = game.getStack().stream()
                            .filter(object -> playerC.getId().equals(object.getControllerId())
                                    || (object instanceof Spell && playerC.getId().equals(((Spell) object).getOwnerId())))
                            .collect(Collectors.toList());
                    Assert.assertTrue(info + " - left on the stack: " + leftOver, leftOver.isEmpty());
                    Assert.assertEquals(info + " - the departed player must not own battlefield objects",
                            0, game.getBattlefield().getAllActivePermanents(playerC.getId()).size());
                });

        setStopAt(4, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLost("PlayerC is removed by the 704.5a life total state-based action", playerC);

        // 800.4b - no permanent is created for a player that already left the game
        assertPermanentCount(playerC, GRIZZLY_BEARS, 0);
        assertPermanentCount(playerB, SILVERCOAT_LION, 1);

        assertNoPriorityForDepartedPlayer("117.5/800.4a");
        assertReceivedPriority("next player in turn order takes over priority", playerB, 3);

        assertTurn(4);
        Assert.assertEquals("turn 4 must be PlayerB's turn (next in turn order after PlayerC)",
                playerB.getId(), currentGame.getActivePlayerId());
    }

    // ------------------------------------------------------------------------------------------
    // Controls: these must be green both before and after the repair, so a green regression above
    // cannot be explained by an empty priority recording or by players being skipped generally.
    // ------------------------------------------------------------------------------------------

    /**
     * Control: with nobody eliminated, every seated player receives priority on both turns.
     */
    @Test
    public void test_fourPlayers_controlAllPlayersInGameReceivePriority() {
        assertActivePlayer(1, PhaseStep.PRECOMBAT_MAIN, playerA, playerA);
        assertActivePlayer(2, PhaseStep.PRECOMBAT_MAIN, playerA, playerD);

        setStopAt(2, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertSeats("PlayerA, PlayerB, PlayerC, PlayerD", 4);
        for (Player player : currentGame.getPlayers().values()) {
            assertInGame(player.getName() + " must still be in the game", player);
            assertReceivedPriority("every player gets priority while nobody left the game", player, 1);
            assertReceivedPriority("every player gets priority while nobody left the game", player, 2);
        }
        assertNoPriorityForDepartedPlayer("control: nobody left the game");
    }

    /**
     * Control: a non-lethal life payment keeps the paying player in the game and keeps its priority
     * loop running, so the green result is not caused by the life payment itself.
     */
    @Test
    public void test_fourPlayers_controlNonLethalLifePaymentKeepsPriorityAndPlayerInGame() {
        assertActivePlayer(1, PhaseStep.PRECOMBAT_MAIN, playerA, playerA);

        setLife(playerA, 20);
        addCard(Zone.BATTLEFIELD, playerA, SHADOWCLOAK_VAMPIRE);
        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, PAY_TWO_LIFE);
        // the same player is asked for priority again after the non-lethal payment
        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, PAY_TWO_LIFE);

        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertSeats("PlayerA, PlayerB, PlayerC, PlayerD", 4);
        assertInGame("PlayerA survives a non-lethal payment", playerA);
        Assert.assertEquals("life payment was really applied", 16, playerA.getLife());
        assertNoPriorityForDepartedPlayer("control: nobody left the game");
        assertReceivedPriority("paying player keeps priority after a non-lethal payment", playerA, 1);
    }

    // ------------------------------------------------------------------------------------------
    // Same scenarios at the other supported table sizes. Turn order is A,B / A,C,B /
    // A,E,D,C,B, so the eliminated player is always PlayerC except in a two player duel, and the
    // next player in turn order is always PlayerB.
    // ------------------------------------------------------------------------------------------

    @Test
    public void test_twoPlayers_departedPlayerGetsNoPriority() {
        assertActivePlayer(1, PhaseStep.PRECOMBAT_MAIN, playerA, playerA);
        // the game ends inside turn 2, so PlayerB is the checker for its own turn
        assertActivePlayer(2, PhaseStep.PRECOMBAT_MAIN, playerB, playerB);

        setupLethalLifePayment(2, playerB);

        setStopAt(2, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertSeats("PlayerA, PlayerB", 2);
        assertLost("PlayerB is removed by the 704.5a life total state-based action", playerB);
        // a winner is no longer "in game" by 104.1, so assert the win instead
        Assert.assertFalse("PlayerA must not have lost", playerA.hasLost());
        Assert.assertTrue("PlayerA wins once the table has a single player left", playerA.hasWon());

        assertReceivedPriority("active player holds priority before elimination", playerB, 2);
        assertNoPriorityForDepartedPlayer("117.5/800.4a");
    }

    @Test
    public void test_threePlayers_activePlayerEliminatedDuringOwnPriorityGetsNoPriority() {
        assertActivePlayer(1, PhaseStep.PRECOMBAT_MAIN, playerA, playerA);
        assertActivePlayer(2, PhaseStep.PRECOMBAT_MAIN, playerA, playerC);
        assertActivePlayer(3, PhaseStep.PRECOMBAT_MAIN, playerA, playerB);

        setupLethalLifePayment(2, playerC);

        checkStackSize("stack during the rest of the departed active player's turn",
                2, PhaseStep.POSTCOMBAT_MAIN, playerB, 0);

        setStopAt(3, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertSeats("PlayerA, PlayerB, PlayerC", 3);
        assertLost("PlayerC is removed by the 704.5a life total state-based action", playerC);
        assertInGame("PlayerA survives", playerA);
        assertInGame("PlayerB survives", playerB);

        assertReceivedPriority("active player holds priority before elimination", playerC, 2);
        assertNoPriorityForDepartedPlayer("117.5/800.4a");
        assertReceivedPriority("next player in turn order takes over priority", playerB, 2);

        assertTurn(3);
        Assert.assertEquals("turn 3 must be PlayerB's turn (next in turn order after PlayerC)",
                playerB.getId(), currentGame.getActivePlayerId());
    }

    @Test
    public void test_fivePlayers_activePlayerEliminatedDuringOwnPriorityGetsNoPriority() {
        assertActivePlayer(1, PhaseStep.PRECOMBAT_MAIN, playerA, playerA);
        assertActivePlayer(2, PhaseStep.PRECOMBAT_MAIN, playerA, playerE);
        assertActivePlayer(3, PhaseStep.PRECOMBAT_MAIN, playerA, playerD);
        assertActivePlayer(4, PhaseStep.PRECOMBAT_MAIN, playerA, playerC);
        assertActivePlayer(5, PhaseStep.PRECOMBAT_MAIN, playerA, playerB);

        setupLethalLifePayment(4, playerC);

        checkStackSize("stack during the rest of the departed active player's turn",
                4, PhaseStep.POSTCOMBAT_MAIN, playerB, 0);

        setStopAt(5, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertSeats("PlayerA, PlayerB, PlayerC, PlayerD, PlayerE", 5);
        assertLost("PlayerC is removed by the 704.5a life total state-based action", playerC);
        assertInGame("PlayerA survives", playerA);
        assertInGame("PlayerB survives", playerB);
        assertInGame("PlayerD survives", playerD);
        assertInGame("PlayerE survives", playerE);

        assertReceivedPriority("active player holds priority before elimination", playerC, 4);
        assertNoPriorityForDepartedPlayer("117.5/800.4a");
        assertReceivedPriority("next player in turn order takes over priority", playerB, 4);

        assertTurn(5);
        Assert.assertEquals("turn 5 must be PlayerB's turn (next in turn order after PlayerC)",
                playerB.getId(), currentGame.getActivePlayerId());
    }

    // ------------------------------------------------------------------------------------------
    // helpers
    // ------------------------------------------------------------------------------------------

    /**
     * Queues a runtime check of the active player of the given turn/step, so the turn order used by
     * the scenario is verified by the engine instead of assumed by the test.
     */
    private void assertActivePlayer(int turn, PhaseStep step, TestPlayer checker, TestPlayer expectedActive) {
        runCode("active player of turn " + turn + " " + step, turn, step, checker, (info, player, game) ->
                Assert.assertEquals("turn order: " + info,
                        expectedActive.getId(), game.getActivePlayerId()));
    }

    /**
     * Gives a player a life total of 2 plus an ability whose only cost is paying 2 life, and queues
     * that ability. The payment (118.3b) brings the life total to 0 and the engine's own state-based
     * action check (704.5a) removes the player while it holds priority.
     */
    private void setupLethalLifePayment(int turn, TestPlayer player) {
        setLife(player, 2);
        // Shadowcloak Vampire {4}{B} 4/3 - Pay 2 life: Shadowcloak Vampire gains flying until end of turn.
        addCard(Zone.BATTLEFIELD, player, SHADOWCLOAK_VAMPIRE);
        activateAbility(turn, PhaseStep.PRECOMBAT_MAIN, player, PAY_TWO_LIFE);
    }

    private void assertSeats(String info, int expectedSeats) {
        List<String> names = currentGame.getPlayers().values().stream()
                .map(Player::getName)
                .collect(Collectors.toList());
        Assert.assertEquals("table size and seating - " + info, expectedSeats, names.size());
    }

    private void assertInGame(String info, Player player) {
        Assert.assertTrue(info + " (" + player.getName() + ")", player.isInGame());
    }

    private void assertLost(String info, Player player) {
        Assert.assertTrue(info + " (" + player.getName() + ")", player.hasLost());
        Assert.assertFalse(info + " (" + player.getName() + ")", player.isInGame());
    }

    private void assertReceivedPriority(String info, Player player, int turn) {
        String prefix = player.getName() + "|T" + turn + "|";
        boolean received = PRIORITY_CALLS.stream().anyMatch(call -> call.startsWith(prefix));
        Assert.assertTrue(info + " - " + player.getName() + " never received priority on turn " + turn
                        + "\n  recorded priority calls:\n    " + String.join("\n    ", PRIORITY_CALLS),
                received);
    }

    /**
     * 117.5 + 800.4a/800.4j: a player that left the game must never be asked for priority.
     */
    private void assertNoPriorityForDepartedPlayer(String info) {
        List<String> illegal = PRIORITY_CALLS.stream()
                .filter(call -> call.endsWith("|inGame=false"))
                .collect(Collectors.toList());
        Assert.assertTrue(info + " - engine requested priority from a player that already left the game:"
                        + "\n    " + String.join("\n    ", illegal),
                illegal.isEmpty());
    }

    /**
     * Observation only: records every priority request the engine makes together with the recorded
     * player's game status at that moment.
     */
    private static class PriorityRecordingPlayer extends TestPlayer {

        PriorityRecordingPlayer(TestComputerPlayer computerPlayer) {
            super(computerPlayer);
        }

        PriorityRecordingPlayer(TestPlayer source) {
            super(source);
        }

        @Override
        public TestPlayer copy() {
            return new PriorityRecordingPlayer(this);
        }

        @Override
        public boolean priority(Game game) {
            PRIORITY_CALLS.add(getName() + "|T" + game.getTurnNum() + "|" + game.getTurnStepType().name()
                    + "|inGame=" + isInGame());
            return super.priority(game);
        }
    }
}