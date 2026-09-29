package org.mage.test.commander.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.command.Dungeon;
import mage.game.mulligan.MulliganType;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * F-20 (Commander Simulator Next): the initiative when its holder leaves the game.
 * <p>
 * CR 726.4 (the initiative): if the player who has the initiative leaves the game, the active
 * player takes the initiative at the same time that player leaves the game. If
 * the active player is leaving the game, the next player in turn order takes
 * the initiative. Taking the initiative this way is still taking it, so "whenever
 * you take the initiative, venture into Undercity" (CR 726.2) triggers for the
 * new holder, and from then on it ventures at the beginning of its upkeep.
 * <p>
 * Rule numbers are inferred: the initiative section follows the monarch's, which
 * is CR 725 in the 2026-09-25 edition the Lab cites (724/725 in 2022 editions).
 * The CR text was not re-read in the session that wrote this test.
 * <p>
 * The holder is White Plume Adventurer's controller ("When White Plume
 * Adventurer enters the battlefield, you take the initiative"). The holder's
 * position in turn order is {@link #holderPosition()}, so the tests do not only
 * exercise the first seat. Turn order is A first, then the seats in reverse
 * creation order (A, N, ..., B), as in {@code CardTestCommander4Players}.
 */
public abstract class InitiativeLeavesGameTestBase extends CardTestPlayerAPIImpl {

    protected static final String WHITE_PLUME = "White Plume Adventurer";
    protected static final String BEARS = "Grizzly Bears";
    protected static final String SECRET_ENTRANCE = "Secret Entrance";
    protected static final List<String> SECOND_ROOMS = Arrays.asList("Forge", "Lost Well");

    protected final List<TestPlayer> seats = new ArrayList<>();

    protected abstract int playerCount();

    /** Zero-based position of the initiative holder in turn order. */
    protected int holderPosition() {
        return 0;
    }

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

    protected List<TestPlayer> turnOrder() {
        List<TestPlayer> order = new ArrayList<>();
        order.add(seats.get(0));
        for (int index = seats.size() - 1; index >= 1; index--) {
            order.add(seats.get(index));
        }
        return order;
    }

    protected TestPlayer inTurnOrder(int position) {
        List<TestPlayer> order = turnOrder();
        return order.get(position % order.size());
    }

    /** The holder casts White Plume Adventurer on its own turn and takes the initiative. */
    protected TestPlayer holderTakesInitiative() {
        TestPlayer holder = inTurnOrder(holderPosition());
        int turn = holderPosition() + 1;
        addCard(Zone.BATTLEFIELD, holder, "Plains", 3);
        addCard(Zone.HAND, holder, WHITE_PLUME);
        castSpell(turn, PhaseStep.PRECOMBAT_MAIN, holder, WHITE_PLUME);
        waitStackResolved(turn, PhaseStep.PRECOMBAT_MAIN);
        return holder;
    }

    protected String roomOf(TestPlayer player) {
        Dungeon dungeon = currentGame.getPlayerDungeon(player.getId());
        return dungeon == null || dungeon.getCurrentRoom() == null ? null : dungeon.getCurrentRoom().getName();
    }

    protected void assertInitiative(TestPlayer expected) {
        Assert.assertEquals("initiative holder", expected.getName(),
                currentGame.getInitiativeId() == null ? null
                        : currentGame.getPlayer(currentGame.getInitiativeId()).getName());
    }

    @Test
    public void holderLeavesOnAnotherPlayersTurn_activePlayerTakesTheInitiative() {
        TestPlayer holder = holderTakesInitiative();
        int turn = holderPosition() + 2;
        TestPlayer active = inTurnOrder(holderPosition() + 1);

        concede(turn, PhaseStep.PRECOMBAT_MAIN, holder);
        setStopAt(turn, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        Assert.assertTrue(holder.getName() + " left", holder.hasLeft());
        Assert.assertEquals("active player", active.getId(), currentGame.getActivePlayerId());
        assertInitiative(active);
        Assert.assertEquals("taking the initiative ventures into Undercity", SECRET_ENTRANCE, roomOf(active));
    }

    @Test
    public void holderLeavesOnItsOwnTurn_nextPlayerInTurnOrderTakesTheInitiative() {
        TestPlayer holder = holderTakesInitiative();
        int turn = holderPosition() + 1;
        TestPlayer next = inTurnOrder(holderPosition() + 1);
        TestPlayer afterNext = inTurnOrder(holderPosition() + 2);

        concede(turn, PhaseStep.POSTCOMBAT_MAIN, holder);
        // The new holder ventures when it takes the initiative and again at its upkeep.
        setStopAt(turn + 1, PhaseStep.PRECOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        Assert.assertTrue(holder.getName() + " left", holder.hasLeft());
        Assert.assertEquals("turn order continues with the next player", next.getId(), currentGame.getActivePlayerId());
        assertInitiative(next);
        Assert.assertTrue("take + upkeep venture reach a second Undercity room, got " + roomOf(next),
                SECOND_ROOMS.contains(roomOf(next)));
        Assert.assertNull("no other player ventured", roomOf(afterNext));
    }

    @Test
    public void anotherPlayerLeaves_theInitiativeStays() {
        TestPlayer holder = holderTakesInitiative();
        int turn = holderPosition() + 2;
        TestPlayer active = inTurnOrder(holderPosition() + 1);
        TestPlayer leaver = inTurnOrder(holderPosition() + 2);

        concede(turn, PhaseStep.PRECOMBAT_MAIN, leaver);
        setStopAt(turn, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        Assert.assertTrue(leaver.getName() + " left", leaver.hasLeft());
        assertInitiative(holder);
        Assert.assertNull("the active player did not take the initiative", roomOf(active));
    }

    @Test
    public void newHolderCanLoseTheInitiativeToCombatDamage() {
        // After the first holder left, the initiative's damage trigger must still work.
        TestPlayer holder = holderTakesInitiative();
        int turn = holderPosition() + 1;
        TestPlayer next = inTurnOrder(holderPosition() + 1);
        TestPlayer attacker = inTurnOrder(holderPosition() + 2);
        addCard(Zone.BATTLEFIELD, attacker, BEARS);

        concede(turn, PhaseStep.POSTCOMBAT_MAIN, holder);
        attack(turn + 2, attacker, BEARS, next);
        setStopAt(turn + 2, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        Assert.assertTrue(holder.getName() + " left", holder.hasLeft());
        assertInitiative(attacker);
        Assert.assertEquals("the attacker ventured when it took the initiative", SECRET_ENTRANCE, roomOf(attacker));
    }
}
