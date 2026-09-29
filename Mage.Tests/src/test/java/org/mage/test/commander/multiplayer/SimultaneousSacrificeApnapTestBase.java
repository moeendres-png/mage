package org.mage.test.commander.multiplayer;

import mage.abilities.Ability;
import mage.constants.MultiplayerAttackOption;
import mage.constants.Outcome;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.target.Target;
import mage.target.common.TargetSacrifice;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * F-21 (Commander Simulator Next): simultaneous "each player / each opponent
 * sacrifices" choices in APNAP order.
 * <p>
 * CR 101.4: if multiple players would make choices and/or take actions at the
 * same time, the active player makes any choices required, then the next
 * player in turn order, followed by the remaining nonactive players in turn
 * order; then the actions happen simultaneously. The order starts with the
 * active player, not with the controller of the effect, so it only coincides
 * with "controller first" when the controller is the active player.
 * <p>
 * Every sacrifice choice is recorded by the choosing player. Turn order is A
 * first, then the seats in reverse creation order (A, N, ..., B), as in
 * {@code CardTestCommander4Players}; each seat controls two creatures so every
 * sacrifice is a real choice.
 */
public abstract class SimultaneousSacrificeApnapTestBase extends CardTestPlayerAPIImpl {

    protected static final String TRIUMPH = "Liliana's Triumph"; // instant: each opponent sacrifices a creature
    protected static final String GRAVE_PACT = "Grave Pact"; // a creature you control dies: each other player sacrifices
    protected static final String INNOCENT_BLOOD = "Innocent Blood"; // sorcery: each player sacrifices a creature
    protected static final String BOLT = "Lightning Bolt";

    /** Players, in the order they chose what to sacrifice. */
    protected final List<String> choosers = new ArrayList<>();
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

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new RecordingPlayer(new TestComputerPlayer(playerName, rangeOfInfluence), this);
    }

    protected List<TestPlayer> turnOrder() {
        List<TestPlayer> order = new ArrayList<>();
        order.add(seats.get(0));
        for (int index = seats.size() - 1; index >= 1; index--) {
            order.add(seats.get(index));
        }
        return order;
    }

    /** CR 101.4: players from the active one in turn order, without {@code excluded}. */
    protected List<String> apnap(TestPlayer active, TestPlayer excluded) {
        List<TestPlayer> order = turnOrder();
        int start = order.indexOf(active);
        List<String> names = new ArrayList<>();
        for (int offset = 0; offset < order.size(); offset++) {
            TestPlayer player = order.get((start + offset) % order.size());
            if (player != excluded) {
                names.add(player.getName());
            }
        }
        return names;
    }

    protected void everyoneHasTwoCreatures() {
        for (TestPlayer seat : seats) {
            addCard(Zone.BATTLEFIELD, seat, "Grizzly Bears", 1);
            addCard(Zone.BATTLEFIELD, seat, "Runeclaw Bear", 1);
        }
    }

    protected void assertChoosers(List<String> expected) {
        Assert.assertEquals("CR 101.4: sacrifice choices in APNAP order", expected, choosers);
        for (TestPlayer seat : seats) {
            if (expected.contains(seat.getName())) {
                long creatures = currentGame.getBattlefield().getAllActivePermanents(seat.getId()).stream()
                        .filter(permanent -> permanent.isCreature(currentGame)).count();
                Assert.assertEquals(seat.getName() + " sacrificed exactly one creature", 1, creatures);
            }
        }
    }

    @Test
    public void eachOpponentSacrifices_firstPlayerCastsOnItsTurn() {
        everyoneHasTwoCreatures();
        TestPlayer caster = turnOrder().get(0);
        addCard(Zone.BATTLEFIELD, caster, "Swamp", 2);
        addCard(Zone.HAND, caster, TRIUMPH);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, caster, TRIUMPH);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        assertChoosers(apnap(caster, caster));
    }

    @Test
    public void eachOpponentSacrifices_thirdPlayerCastsOnItsTurn() {
        everyoneHasTwoCreatures();
        TestPlayer caster = turnOrder().get(2);
        addCard(Zone.BATTLEFIELD, caster, "Swamp", 2);
        addCard(Zone.HAND, caster, TRIUMPH);
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, caster, TRIUMPH);
        setStopAt(3, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        assertChoosers(apnap(caster, caster));
    }

    @Test
    public void eachOpponentSacrifices_nonActiveCasterStartsWithTheActivePlayer() {
        everyoneHasTwoCreatures();
        TestPlayer active = turnOrder().get(0);
        TestPlayer caster = turnOrder().get(2);
        addCard(Zone.BATTLEFIELD, caster, "Swamp", 2);
        addCard(Zone.HAND, caster, TRIUMPH);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, caster, TRIUMPH);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        assertChoosers(apnap(active, caster));
    }

    @Test
    public void gravePactOnAnotherPlayersTurnStartsWithTheActivePlayer() {
        everyoneHasTwoCreatures();
        TestPlayer active = turnOrder().get(0);
        TestPlayer pactController = turnOrder().get(2);
        addCard(Zone.BATTLEFIELD, pactController, GRAVE_PACT);
        addCard(Zone.BATTLEFIELD, pactController, "Raging Goblin");
        addCard(Zone.BATTLEFIELD, active, "Mountain", 1);
        addCard(Zone.HAND, active, BOLT);
        // a creature of the Grave Pact controller dies on the active player's turn
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, active, BOLT, "Raging Goblin");
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        assertGraveyardCount(pactController, "Raging Goblin", 1);
        assertChoosers(apnap(active, pactController));
    }

    @Test
    public void eachPlayerSacrifices_activeCasterIsFirst() {
        everyoneHasTwoCreatures();
        TestPlayer caster = turnOrder().get(2);
        addCard(Zone.BATTLEFIELD, caster, "Swamp", 1);
        addCard(Zone.HAND, caster, INNOCENT_BLOOD);
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, caster, INNOCENT_BLOOD);
        setStopAt(3, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        assertChoosers(apnap(caster, null));
    }

    /** Test player that records each sacrifice choice. */
    static final class RecordingPlayer extends TestPlayer {

        private final transient SimultaneousSacrificeApnapTestBase test;

        RecordingPlayer(TestComputerPlayer computerPlayer, SimultaneousSacrificeApnapTestBase test) {
            super(computerPlayer);
            this.test = test;
        }

        private RecordingPlayer(RecordingPlayer player) {
            super(player);
            this.test = player.test;
        }

        @Override
        public boolean choose(Outcome outcome, Target target, Ability source, Game game, Map<String, Serializable> options) {
            if (target instanceof TargetSacrifice
                    && (test.choosers.isEmpty() || !test.choosers.get(test.choosers.size() - 1).equals(getName()))) {
                test.choosers.add(getName());
            }
            return super.choose(outcome, target, source, game, options);
        }

        @Override
        public RecordingPlayer copy() {
            return new RecordingPlayer(this);
        }
    }
}
