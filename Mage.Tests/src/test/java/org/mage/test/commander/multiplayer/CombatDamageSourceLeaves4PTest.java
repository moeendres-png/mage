package org.mage.test.commander.multiplayer;

import mage.constants.MultiAmountType;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.util.MultiAmountMessage;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestCommander4Players;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * F-43 / CR 800.4a: a permanent whose controller leaves during a combat-damage
 * assignment callback must not keep dealing damage through a cached Permanent.
 *
 * The same inherited cases are also executed at 5P by CombatDamageSourceLeaves5PTest.
 */
public class CombatDamageSourceLeaves4PTest extends CardTestCommander4Players {

    private static final String CRAW_WURM = "Craw Wurm";
    private static final String GRIZZLY = "Grizzly Bears";
    private static final String RUNECLAW = "Runeclaw Bear";

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new ConcedeOnMultiAmountPlayer(new TestComputerPlayer(playerName, rangeOfInfluence));
    }

    private ConcedeOnMultiAmountPlayer arm(TestPlayer player, String sourceName) {
        ConcedeOnMultiAmountPlayer testPlayer = (ConcedeOnMultiAmountPlayer) player;
        testPlayer.concedeOnNextMultiAmountChoice(sourceName);
        return testPlayer;
    }

    private void assertLifetimeTrace(ConcedeOnMultiAmountPlayer leaver, TestPlayer expectedController) {
        Assert.assertNotNull("combat damage source id captured before concession", leaver.damageSourceId);
        Assert.assertEquals("source controller captured before concession",
                expectedController.getId(), leaver.damageSourceControllerId);
        Assert.assertTrue("source was present before concession", leaver.damageSourcePresentBeforeConcede);
        Assert.assertTrue("controller was in game before concession", leaver.controllerInGameBeforeConcede);
        Assert.assertTrue("controller could respond before concession", leaver.controllerCanRespondBeforeConcede);
        Assert.assertFalse("same source is absent after CR 800.4a leave", leaver.damageSourcePresentAfterConcede);
        Assert.assertFalse("controller is no longer in game after concession", leaver.controllerInGameAfterConcede);
        Assert.assertFalse("controller can no longer respond after concession", leaver.controllerCanRespondAfterConcede);
        Assert.assertNotNull("multi_amount header captured", leaver.multiAmountHeader);
        Assert.assertNotNull("explicit legal assignment captured", leaver.returnedAmounts);
    }

    /**
     * Exact F-42 follow-up-3 reproducer: Craw Wurm attacks into Grizzly Bears +
     * Runeclaw Bear and P1 leaves inside the multi_amount callback.
     */
    @Test
    public void attackingCrawWurmLeavesDuringDamageDivision() {
        addCard(Zone.BATTLEFIELD, playerA, CRAW_WURM); // 6/4
        addCard(Zone.BATTLEFIELD, playerB, GRIZZLY);   // 2/2
        addCard(Zone.BATTLEFIELD, playerB, RUNECLAW);  // 2/2

        attack(1, playerA, CRAW_WURM, playerB);
        block(1, playerB, GRIZZLY, CRAW_WURM);
        block(1, playerB, RUNECLAW, CRAW_WURM);

        // Explicit legal current-rules division totaling six. The choice is
        // consumed while A is still in the game. The test player concedes only
        // after super returns the legal vector, but before CombatGroup receives it.
        setChoiceAmount(playerA, 3, 3);
        ConcedeOnMultiAmountPlayer leaver = arm(playerA, CRAW_WURM);

        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertLostTheGame(playerA);
        Assert.assertFalse("remaining multiplayer game continues", currentGame.hasEnded());
        assertLifetimeTrace(leaver, playerA);
        Assert.assertEquals("exact multi_amount vector", List.of(3, 3), leaver.returnedAmounts);
        assertPermanentCount(playerB, GRIZZLY, 1);
        assertPermanentCount(playerB, RUNECLAW, 1);
        assertDamageReceived(playerB, GRIZZLY, 0);
        assertDamageReceived(playerB, RUNECLAW, 0);
    }

    /** Mirror stale-source direction: one blocker divides damage among two attackers. */
    @Test
    public void blockingSourceLeavesDuringDamageDivision() {
        addCard(Zone.BATTLEFIELD, playerA, GRIZZLY);
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion");
        addCard(Zone.BATTLEFIELD, playerB, "Brave the Sands");
        addCard(Zone.BATTLEFIELD, playerB, "Marsh Hulk"); // 4/6, can block two

        attack(1, playerA, GRIZZLY, playerB);
        attack(1, playerA, "Silvercoat Lion", playerB);
        block(1, playerB, "Marsh Hulk", GRIZZLY);
        block(1, playerB, "Marsh Hulk", "Silvercoat Lion");

        setChoiceAmount(playerB, 2, 2);
        ConcedeOnMultiAmountPlayer leaver = arm(playerB, "Marsh Hulk");

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLostTheGame(playerB);
        Assert.assertFalse("remaining multiplayer game continues", currentGame.hasEnded());
        assertLifetimeTrace(leaver, playerB);
        assertPermanentCount(playerA, GRIZZLY, 1);
        assertPermanentCount(playerA, "Silvercoat Lion", 1);
        assertDamageReceived(playerA, GRIZZLY, 0);
        assertDamageReceived(playerA, "Silvercoat Lion", 0);
    }

    /** Trample must not leak cached blocker or through-damage after the source leaves. */
    @Test
    public void tramplingSourceLeavesDuringDamageDivision() {
        addCard(Zone.BATTLEFIELD, playerA, "Colossal Dreadmaw"); // 6/6 trample
        addCard(Zone.BATTLEFIELD, playerB, GRIZZLY);
        addCard(Zone.BATTLEFIELD, playerB, RUNECLAW);

        attack(1, playerA, "Colossal Dreadmaw", playerB);
        block(1, playerB, GRIZZLY, "Colossal Dreadmaw");
        block(1, playerB, RUNECLAW, "Colossal Dreadmaw");

        // Four to blockers, two would trample through if the stale source were used.
        setChoiceAmount(playerA, 2, 2);
        ConcedeOnMultiAmountPlayer leaver = arm(playerA, "Colossal Dreadmaw");

        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertLostTheGame(playerA);
        assertLifetimeTrace(leaver, playerA);
        assertLife(playerB, 20);
        assertDamageReceived(playerB, GRIZZLY, 0);
        assertDamageReceived(playerB, RUNECLAW, 0);
    }

    /** First-strike damage assignment crosses the same callback boundary. */
    @Test
    public void firstStrikeSourceLeavesDuringDamageDivision() {
        addCard(Zone.BATTLEFIELD, playerA, "White Knight"); // 2/2 first strike
        addCard(Zone.BATTLEFIELD, playerB, GRIZZLY);
        addCard(Zone.BATTLEFIELD, playerB, RUNECLAW);

        attack(1, playerA, "White Knight", playerB);
        block(1, playerB, GRIZZLY, "White Knight");
        block(1, playerB, RUNECLAW, "White Knight");

        setChoiceAmount(playerA, 1, 1);
        ConcedeOnMultiAmountPlayer leaver = arm(playerA, "White Knight");

        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertLostTheGame(playerA);
        assertLifetimeTrace(leaver, playerA);
        assertDamageReceived(playerB, GRIZZLY, 0);
        assertDamageReceived(playerB, RUNECLAW, 0);
    }

    /** Double-strike first damage step must not retain the departed source. */
    @Test
    public void doubleStrikeSourceLeavesDuringDamageDivision() {
        addCard(Zone.BATTLEFIELD, playerA, "Warren Instigator"); // 1/1 double strike
        addCard(Zone.BATTLEFIELD, playerB, GRIZZLY);
        addCard(Zone.BATTLEFIELD, playerB, RUNECLAW);

        attack(1, playerA, "Warren Instigator", playerB);
        block(1, playerB, GRIZZLY, "Warren Instigator");
        block(1, playerB, RUNECLAW, "Warren Instigator");

        setChoiceAmount(playerA, 1, 0);
        ConcedeOnMultiAmountPlayer leaver = arm(playerA, "Warren Instigator");

        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertLostTheGame(playerA);
        assertLifetimeTrace(leaver, playerA);
        assertDamageReceived(playerB, GRIZZLY, 0);
        assertDamageReceived(playerB, RUNECLAW, 0);
    }

    static final class ConcedeOnMultiAmountPlayer extends TestPlayer {

        private boolean concedeOnNextMultiAmountChoice;
        private String expectedDamageSourceName;

        private UUID damageSourceId;
        private UUID damageSourceControllerId;
        private boolean damageSourcePresentBeforeConcede;
        private boolean controllerInGameBeforeConcede;
        private boolean controllerCanRespondBeforeConcede;
        private boolean damageSourcePresentAfterConcede;
        private boolean controllerInGameAfterConcede;
        private boolean controllerCanRespondAfterConcede;
        private String multiAmountHeader;
        private List<Integer> returnedAmounts;

        private ConcedeOnMultiAmountPlayer(TestComputerPlayer computerPlayer) {
            super(computerPlayer);
        }

        private ConcedeOnMultiAmountPlayer(ConcedeOnMultiAmountPlayer player) {
            super(player);
            this.concedeOnNextMultiAmountChoice = player.concedeOnNextMultiAmountChoice;
            this.expectedDamageSourceName = player.expectedDamageSourceName;
            this.damageSourceId = player.damageSourceId;
            this.damageSourceControllerId = player.damageSourceControllerId;
            this.damageSourcePresentBeforeConcede = player.damageSourcePresentBeforeConcede;
            this.controllerInGameBeforeConcede = player.controllerInGameBeforeConcede;
            this.controllerCanRespondBeforeConcede = player.controllerCanRespondBeforeConcede;
            this.damageSourcePresentAfterConcede = player.damageSourcePresentAfterConcede;
            this.controllerInGameAfterConcede = player.controllerInGameAfterConcede;
            this.controllerCanRespondAfterConcede = player.controllerCanRespondAfterConcede;
            this.multiAmountHeader = player.multiAmountHeader;
            this.returnedAmounts = player.returnedAmounts == null ? null : new ArrayList<>(player.returnedAmounts);
        }

        void concedeOnNextMultiAmountChoice(String sourceName) {
            this.concedeOnNextMultiAmountChoice = true;
            this.expectedDamageSourceName = sourceName;
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
            // Obtain and validate the player's explicit choice while the player is
            // still authoritative. Concession occurs inside this callback only after
            // that choice is complete, before CombatGroup can consume the vector.
            List<Integer> answer = super.getMultiAmountWithIndividualConstraints(
                    outcome, messages, totalMin, totalMax, type, game
            );
            if (!concedeOnNextMultiAmountChoice) {
                return answer;
            }

            concedeOnNextMultiAmountChoice = false;
            Permanent source = game.getBattlefield().getAllActivePermanents().stream()
                    .filter(permanent -> permanent.getName().equals(expectedDamageSourceName))
                    .filter(permanent -> permanent.getControllerId().equals(getId()))
                    .findFirst()
                    .orElse(null);
            Assert.assertNotNull("armed combat-damage source exists before concession", source);

            damageSourceId = source.getId();
            damageSourceControllerId = source.getControllerId();
            damageSourcePresentBeforeConcede = game.getPermanent(damageSourceId) != null;
            Player controllerBefore = game.getPlayer(damageSourceControllerId);
            controllerInGameBeforeConcede = controllerBefore != null && controllerBefore.isInGame();
            controllerCanRespondBeforeConcede = controllerBefore != null && controllerBefore.canRespond();
            multiAmountHeader = type.getHeader();
            returnedAmounts = new ArrayList<>(answer);

            game.concede(getId());

            damageSourcePresentAfterConcede = game.getPermanent(damageSourceId) != null;
            Player controllerAfter = game.getPlayer(damageSourceControllerId);
            controllerInGameAfterConcede = controllerAfter != null && controllerAfter.isInGame();
            controllerCanRespondAfterConcede = controllerAfter != null && controllerAfter.canRespond();

            System.out.println(
                    "F43_TRACE source=" + expectedDamageSourceName
                            + " sourceId=" + damageSourceId
                            + " controllerId=" + damageSourceControllerId
                            + " multiAmountHeader=" + multiAmountHeader
                            + " returnedAmounts=" + returnedAmounts
                            + " sourcePresentBefore=" + damageSourcePresentBeforeConcede
                            + " controllerInGameBefore=" + controllerInGameBeforeConcede
                            + " controllerCanRespondBefore=" + controllerCanRespondBeforeConcede
                            + " sourcePresentAfter=" + damageSourcePresentAfterConcede
                            + " controllerInGameAfter=" + controllerInGameAfterConcede
                            + " controllerCanRespondAfter=" + controllerCanRespondAfterConcede
                            + " damageMarkedBeforeCombatGroupResume=0"
            );
            return answer;
        }

        @Override
        public ConcedeOnMultiAmountPlayer copy() {
            return new ConcedeOnMultiAmountPlayer(this);
        }
    }
}
