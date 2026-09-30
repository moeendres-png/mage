package org.mage.test.commander.multiplayer;

import mage.MultiAmountType;
import mage.constants.MultiplayerAttackOption;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.util.MultiAmountMessage;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * F-43 / F-42 follow-up 3: a combat-damage source must be revalidated after
 * a player-controlled damage-assignment decision. If its controller concedes
 * inside that decision, CR 800.4a removes the source before the decision
 * returns and the stale Java object must not subsequently mark combat damage.
 */
public abstract class CombatDamageLeaverTestBase extends CardTestPlayerAPIImpl {

    private static final String ATTACKER = "Craw Wurm";
    private static final String BLOCKER_ONE = "Grizzly Bears";
    private static final String BLOCKER_TWO = "Runeclaw Bear";

    private final List<TestPlayer> seats = new ArrayList<>();

    protected abstract int playerCount();

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new ConcedeDuringMultiAmountPlayer(new TestComputerPlayer(playerName, rangeOfInfluence));
    }

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new CommanderFreeForAll(
                MultiplayerAttackOption.MULTIPLE,
                RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0),
                40,
                7
        );
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

    @Test
    public void departedAttackerDoesNotDealCachedDamageAfterMultiAmountDecision() {
        addCard(Zone.BATTLEFIELD, playerA, ATTACKER);
        addCard(Zone.BATTLEFIELD, playerB, BLOCKER_ONE);
        addCard(Zone.BATTLEFIELD, playerB, BLOCKER_TWO);

        attack(1, playerA, ATTACKER, playerB);
        block(1, playerB, BLOCKER_ONE, ATTACKER);
        block(1, playerB, BLOCKER_TWO, ATTACKER);

        setChoiceAmount(playerA, 3, 3);
        ((ConcedeDuringMultiAmountPlayer) playerA).concedeDuringNextMultiAmount();

        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();

        ConcedeDuringMultiAmountPlayer leaver = (ConcedeDuringMultiAmountPlayer) playerA;
        Assert.assertTrue("attacker controller left during multi_amount", playerA.hasLeft());
        Assert.assertNotNull("attacker id captured before concession", leaver.damageSourceId);
        Assert.assertEquals("attacker controller captured", playerA.getId(), leaver.damageSourceControllerId);
        Assert.assertTrue("attacker present before decision-side concession", leaver.damageSourcePresentBeforeConcede);
        Assert.assertTrue("controller was in game before concession", leaver.controllerInGameBeforeConcede);
        Assert.assertTrue("controller could respond before concession", leaver.controllerCanRespondBeforeConcede);
        Assert.assertFalse("attacker absent immediately after CR 800.4a leave", leaver.damageSourcePresentAfterConcede);
        Assert.assertFalse("controller no longer in game after concession", leaver.controllerInGameAfterConcede);
        Assert.assertFalse("controller cannot respond after concession", leaver.controllerCanRespondAfterConcede);

        assertPermanentCount(playerB, BLOCKER_ONE, 1);
        assertPermanentCount(playerB, BLOCKER_TWO, 1);
        assertDamageReceived(playerB, BLOCKER_ONE, 0);
        assertDamageReceived(playerB, BLOCKER_TWO, 0);
    }

    static final class ConcedeDuringMultiAmountPlayer extends TestPlayer {

        private boolean concedeOnNextMultiAmount;

        private UUID damageSourceId;
        private UUID damageSourceControllerId;
        private boolean damageSourcePresentBeforeConcede;
        private boolean controllerInGameBeforeConcede;
        private boolean controllerCanRespondBeforeConcede;
        private boolean damageSourcePresentAfterConcede;
        private boolean controllerInGameAfterConcede;
        private boolean controllerCanRespondAfterConcede;

        ConcedeDuringMultiAmountPlayer(TestComputerPlayer computerPlayer) {
            super(computerPlayer);
        }

        private ConcedeDuringMultiAmountPlayer(ConcedeDuringMultiAmountPlayer player) {
            super(player);
            this.concedeOnNextMultiAmount = player.concedeOnNextMultiAmount;
            this.damageSourceId = player.damageSourceId;
            this.damageSourceControllerId = player.damageSourceControllerId;
            this.damageSourcePresentBeforeConcede = player.damageSourcePresentBeforeConcede;
            this.controllerInGameBeforeConcede = player.controllerInGameBeforeConcede;
            this.controllerCanRespondBeforeConcede = player.controllerCanRespondBeforeConcede;
            this.damageSourcePresentAfterConcede = player.damageSourcePresentAfterConcede;
            this.controllerInGameAfterConcede = player.controllerInGameAfterConcede;
            this.controllerCanRespondAfterConcede = player.controllerCanRespondAfterConcede;
        }

        void concedeDuringNextMultiAmount() {
            this.concedeOnNextMultiAmount = true;
        }

        @Override
        public List<Integer> getMultiAmountWithIndividualConstraints(
                Outcome outcome,
                List<MultiAmountMessage> messages,
                int totalMin,
                int totalMax,
                MultiAmountType type,
                Game game
        ) {
            List<Integer> answer = super.getMultiAmountWithIndividualConstraints(
                    outcome, messages, totalMin, totalMax, type, game
            );
            if (!concedeOnNextMultiAmount) {
                return answer;
            }

            concedeOnNextMultiAmount = false;
            Permanent source = game.getBattlefield().getAllActivePermanents().stream()
                    .filter(permanent -> permanent.getName().equals(ATTACKER))
                    .filter(permanent -> permanent.getControllerId().equals(getId()))
                    .findFirst()
                    .orElse(null);

            Assert.assertNotNull("damage source must exist before in-decision concession", source);
            damageSourceId = source.getId();
            damageSourceControllerId = source.getControllerId();
            damageSourcePresentBeforeConcede = game.getPermanent(damageSourceId) != null;
            Player controllerBefore = game.getPlayer(damageSourceControllerId);
            controllerInGameBeforeConcede = controllerBefore != null && controllerBefore.isInGame();
            controllerCanRespondBeforeConcede = controllerBefore != null && controllerBefore.canRespond();

            game.concede(getId());

            damageSourcePresentAfterConcede = game.getPermanent(damageSourceId) != null;
            Player controllerAfter = game.getPlayer(damageSourceControllerId);
            controllerInGameAfterConcede = controllerAfter != null && controllerAfter.isInGame();
            controllerCanRespondAfterConcede = controllerAfter != null && controllerAfter.canRespond();
            return answer;
        }

        @Override
        public ConcedeDuringMultiAmountPlayer copy() {
            return new ConcedeDuringMultiAmountPlayer(this);
        }
    }
}
