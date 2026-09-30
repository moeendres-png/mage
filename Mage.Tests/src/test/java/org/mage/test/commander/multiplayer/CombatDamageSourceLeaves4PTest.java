package org.mage.test.commander.multiplayer;

import mage.constants.MultiAmountType;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import mage.util.MultiAmountMessage;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestCommander4Players;

import java.util.List;

/**
 * F-43 / CR 800.4a: a permanent whose controller leaves during a combat-damage
 * assignment callback must not keep dealing damage through a cached Permanent.
 */
public class CombatDamageSourceLeaves4PTest extends CardTestCommander4Players {

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new ConcedeOnMultiAmountPlayer(new TestComputerPlayer(playerName, rangeOfInfluence));
    }

    @Test
    public void attackingSourceLeavesDuringDamageDivision() {
        addCard(Zone.BATTLEFIELD, playerA, "Alpine Grizzly"); // 4/2
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "Alpine Grizzly", playerB);
        block(1, playerB, "Grizzly Bears", "Alpine Grizzly");
        block(1, playerB, "Silvercoat Lion", "Alpine Grizzly");

        setChoiceAmount(playerA, 2, 2);
        ((ConcedeOnMultiAmountPlayer) playerA).concedeOnNextMultiAmountChoice();

        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertLostTheGame(playerA);
        Assert.assertFalse("the remaining three-player game must continue", currentGame.hasEnded());
        assertPermanentCount(playerB, "Grizzly Bears", 1);
        assertPermanentCount(playerB, "Silvercoat Lion", 1);
        assertDamageReceived(playerB, "Grizzly Bears", 0);
        assertDamageReceived(playerB, "Silvercoat Lion", 0);
    }

    @Test
    public void blockingSourceLeavesDuringDamageDivision() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Brave the Sands");
        addCard(Zone.BATTLEFIELD, playerB, "Marsh Hulk"); // 4/6, can block two via Brave the Sands

        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Silvercoat Lion", playerB);
        block(1, playerB, "Marsh Hulk", "Grizzly Bears");
        block(1, playerB, "Marsh Hulk", "Silvercoat Lion");

        setChoiceAmount(playerB, 2, 2);
        ((ConcedeOnMultiAmountPlayer) playerB).concedeOnNextMultiAmountChoice();

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLostTheGame(playerB);
        Assert.assertFalse("the remaining three-player game must continue", currentGame.hasEnded());
        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertPermanentCount(playerA, "Silvercoat Lion", 1);
        assertDamageReceived(playerA, "Grizzly Bears", 0);
        assertDamageReceived(playerA, "Silvercoat Lion", 0);
    }

    private static final class ConcedeOnMultiAmountPlayer extends TestPlayer {

        private boolean concedeOnNextMultiAmountChoice;

        private ConcedeOnMultiAmountPlayer(TestComputerPlayer computerPlayer) {
            super(computerPlayer);
        }

        private ConcedeOnMultiAmountPlayer(ConcedeOnMultiAmountPlayer player) {
            super(player);
            this.concedeOnNextMultiAmountChoice = player.concedeOnNextMultiAmountChoice;
        }

        void concedeOnNextMultiAmountChoice() {
            this.concedeOnNextMultiAmountChoice = true;
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
            if (concedeOnNextMultiAmountChoice) {
                concedeOnNextMultiAmountChoice = false;
                game.concede(getId());
            }
            return super.getMultiAmountWithIndividualConstraints(
                    outcome, messages, totalMin, totalMax, type, game
            );
        }

        @Override
        public ConcedeOnMultiAmountPlayer copy() {
            return new ConcedeOnMultiAmountPlayer(this);
        }
    }
}
