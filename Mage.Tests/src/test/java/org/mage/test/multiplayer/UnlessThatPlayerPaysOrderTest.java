package org.mage.test.multiplayer;

import mage.abilities.Ability;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestCommander4Players;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * F-19 (Commander Simulator Next): "you may draw a card unless that player pays {N}".
 * <p>
 * Official rulings (Rhystic Study, Mystic Remora): the player gets the option to pay
 * when the ability resolves, and the controller doesn't decide whether to draw until
 * after that player decides whether to pay. The engine asked the controller first,
 * which leaked the controller's intent to the payer and skipped the payment decision
 * whenever the controller declined.
 * <p>
 * Four players, turn order A -> D -> C -> B; the paying opponent C is not the active
 * player. A recording player logs every "Pay" / "Draw" question in order.
 */
public class UnlessThatPlayerPaysOrderTest extends CardTestCommander4Players {

    /** A draws in its turn-1 draw step (multiplayer: no first-draw skip, CR 103.8c). */
    private static final int TURN_DRAW = 1;
    private final List<String> asks = new ArrayList<>();
    /** answers keyed by "Player:prefix" where prefix is "Pay" or "Draw". */
    private final Map<String, Boolean> answers = new HashMap<>();

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new RecordingPlayer(new TestComputerPlayer(playerName, rangeOfInfluence), this);
    }

    private void opponentCastsShock(String enchantment, int opponentMountains) {
        addCard(Zone.BATTLEFIELD, playerA, enchantment, 1);
        if ("Mystic Remora".equals(enchantment)) {
            // Cumulative upkeep {1} in A's first upkeep: A pays it with an Island.
            addCard(Zone.BATTLEFIELD, playerA, "Island", 1);
            answers.put("PlayerA:Pay", true);
        }
        addCard(Zone.HAND, playerC, "Shock", 1);
        addCard(Zone.BATTLEFIELD, playerC, "Mountain", opponentMountains);
        // C (not active) casts on A's turn, targeting B.
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerC, "Shock", playerB);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
    }

    @Test
    public void rhysticPayerPaysFirstAndControllerIsNeverAsked() {
        answers.put("PlayerC:Pay", true);
        opponentCastsShock("Rhystic Study", 2);
        execute();

        Assert.assertEquals(Arrays.asList("PlayerC:Pay"), asks);
        assertHandCount(playerA, TURN_DRAW + 0);
        assertTappedCount("Mountain", true, 2);
        assertLife(playerB, 20 - 2);
    }

    @Test
    public void rhysticPayerDeclinesThenControllerChoosesToDraw() {
        answers.put("PlayerC:Pay", false);
        answers.put("PlayerA:Draw", true);
        opponentCastsShock("Rhystic Study", 2);
        execute();

        Assert.assertEquals(Arrays.asList("PlayerC:Pay", "PlayerA:Draw"), asks);
        assertHandCount(playerA, TURN_DRAW + 1);
        assertTappedCount("Mountain", true, 1);
    }

    @Test
    public void rhysticPayerDeclinesThenControllerMayDecline() {
        answers.put("PlayerC:Pay", false);
        answers.put("PlayerA:Draw", false);
        opponentCastsShock("Rhystic Study", 2);
        execute();

        Assert.assertEquals(Arrays.asList("PlayerC:Pay", "PlayerA:Draw"), asks);
        assertHandCount(playerA, TURN_DRAW + 0);
    }

    @Test
    public void rhysticPayerUnableToPayStillLetsTheControllerDraw() {
        answers.put("PlayerC:Pay", true); // willing, but the only Mountain paid for Shock
        answers.put("PlayerA:Draw", true);
        opponentCastsShock("Rhystic Study", 1);
        execute();

        Assert.assertEquals(Arrays.asList("PlayerC:Pay", "PlayerA:Draw"), asks);
        assertHandCount(playerA, TURN_DRAW + 1);
    }

    @Test
    public void mysticRemoraPayerPaysFourFirst() {
        answers.put("PlayerC:Pay", true);
        opponentCastsShock("Mystic Remora", 5);
        execute();

        Assert.assertEquals(Arrays.asList("PlayerA:Pay", "PlayerC:Pay"), asks);
        assertPermanentCount(playerA, "Mystic Remora", 1);
        assertHandCount(playerA, TURN_DRAW + 0);
        assertTappedCount("Mountain", true, 5);
    }

    @Test
    public void mysticRemoraPayerDeclinesThenControllerDraws() {
        answers.put("PlayerC:Pay", false);
        answers.put("PlayerA:Draw", true);
        opponentCastsShock("Mystic Remora", 5);
        execute();

        Assert.assertEquals(Arrays.asList("PlayerA:Pay", "PlayerC:Pay", "PlayerA:Draw"), asks);
        assertPermanentCount(playerA, "Mystic Remora", 1);
        assertHandCount(playerA, TURN_DRAW + 1);
    }

    /** Records and answers the unless-cost and may-draw questions by player. */
    static final class RecordingPlayer extends TestPlayer {

        private final transient UnlessThatPlayerPaysOrderTest test;

        RecordingPlayer(TestComputerPlayer computerPlayer, UnlessThatPlayerPaysOrderTest test) {
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
            if (message != null && (message.startsWith("Pay {") || message.startsWith("Draw a card ("))) {
                String key = getName() + ":" + (message.startsWith("Pay") ? "Pay" : "Draw");
                Boolean answer = test.answers.get(key);
                if (answer == null) {
                    Assert.fail("unexpected question to " + getName() + ": " + message
                            + " (asked so far: " + test.asks + ")");
                }
                test.asks.add(key);
                return answer;
            }
            return super.chooseUse(outcome, message, secondMessage, trueText, falseText, source, game);
        }

        @Override
        public RecordingPlayer copy() {
            return new RecordingPlayer(this);
        }
    }
}
