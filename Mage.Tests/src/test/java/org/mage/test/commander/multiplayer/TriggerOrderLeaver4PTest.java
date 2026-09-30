package org.mage.test.commander.multiplayer;

import mage.abilities.TriggeredAbility;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestCommander4Players;

import java.util.List;

/**
 * F-44 / CR 800.4a: a player who leaves the game while ordering its own
 * simultaneous triggered abilities must not have any of them put on the stack.
 * <p>
 * {@code GameImpl.checkTriggered} asked {@code chooseTriggeredAbility} and then
 * put the returned ability on the stack without checking that its controller
 * could still respond. A player who conceded inside that choice therefore still
 * had one trigger resolve: here Impact Tremors, whose source had already left
 * the game with its owner, dealt 1 damage to every remaining opponent.
 */
public class TriggerOrderLeaver4PTest extends CardTestCommander4Players {

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new ConcedeOnTriggerOrderPlayer(new TestComputerPlayer(playerName, rangeOfInfluence));
    }

    private void castBearsWithTwoEnterTriggers() {
        // Impact Tremors: whenever a creature you control enters, 1 damage to each opponent.
        // Purphoros, God of the Forge: whenever another creature you control enters,
        // 2 damage to each opponent.
        addCard(Zone.BATTLEFIELD, playerA, "Impact Tremors");
        addCard(Zone.BATTLEFIELD, playerA, "Purphoros, God of the Forge");
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);
        addCard(Zone.HAND, playerA, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Grizzly Bears");
        setChoice(playerA, "Impact Tremors"); // put Impact Tremors' trigger on the stack first
    }

    @Test
    public void bothTriggersResolveWhileTheirControllerStays() {
        castBearsWithTwoEnterTriggers();

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        int start = currentGame.getStartingLife();
        assertLife(playerB, start - 3);
        assertLife(playerC, start - 3);
        assertLife(playerD, start - 3);
    }

    @Test
    public void noTriggerOfAPlayerWhoLeftWhileOrderingThemResolves() {
        castBearsWithTwoEnterTriggers();
        ((ConcedeOnTriggerOrderPlayer) playerA).concedeOnNextTriggerOrder();

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLostTheGame(playerA);
        Assert.assertFalse("the remaining three-player game must continue", currentGame.hasEnded());
        int start = currentGame.getStartingLife();
        assertLife(playerB, start);
        assertLife(playerC, start);
        assertLife(playerD, start);
    }

    private static final class ConcedeOnTriggerOrderPlayer extends TestPlayer {

        private boolean concedeOnNextTriggerOrder;

        private ConcedeOnTriggerOrderPlayer(TestComputerPlayer computerPlayer) {
            super(computerPlayer);
        }

        private ConcedeOnTriggerOrderPlayer(ConcedeOnTriggerOrderPlayer player) {
            super(player);
            this.concedeOnNextTriggerOrder = player.concedeOnNextTriggerOrder;
        }

        void concedeOnNextTriggerOrder() {
            this.concedeOnNextTriggerOrder = true;
        }

        @Override
        public TriggeredAbility chooseTriggeredAbility(List<TriggeredAbility> abilities, Game game) {
            TriggeredAbility chosen = super.chooseTriggeredAbility(abilities, game);
            if (concedeOnNextTriggerOrder) {
                concedeOnNextTriggerOrder = false;
                game.concede(getId());
            }
            return chosen;
        }

        @Override
        public ConcedeOnTriggerOrderPlayer copy() {
            return new ConcedeOnTriggerOrderPlayer(this);
        }
    }
}
