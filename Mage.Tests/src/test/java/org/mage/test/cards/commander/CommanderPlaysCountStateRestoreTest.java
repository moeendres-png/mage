package org.mage.test.cards.commander;

import mage.abilities.Ability;
import mage.abilities.dynamicvalue.common.CommanderCastCountValue;
import mage.cards.Card;
import mage.constants.CommanderCardType;
import mage.constants.PhaseStep;
import mage.constants.WatcherScope;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.Game;
import mage.game.GameState;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.watchers.Watcher;
import mage.watchers.common.CommanderPlaysCountState;
import mage.watchers.common.CommanderPlaysCountWatcher;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommander4PlayersWithAIHelps;

import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;

public class CommanderPlaysCountStateRestoreTest extends CardTestCommander4PlayersWithAIHelps {

    private static final String ROGRAKH = "Rograkh, Son of Rohgahh";
    private static final String JESKA = "Jeska, Thrice Reborn";

    private static UUID commanderId(Game game, Player player, String name) {
        return game.getCommandersIds(player, CommanderCardType.ANY, false)
                .stream()
                .filter(id -> {
                    Card card = game.getCard(id);
                    return card != null && name.equals(card.getName());
                })
                .findFirst()
                .orElseThrow(() -> new AssertionError("Commander not found: " + name));
    }

    private static CommanderPlaysCountWatcher watcher(Game game) {
        CommanderPlaysCountWatcher watcher = game.getState().getWatcher(CommanderPlaysCountWatcher.class);
        Assert.assertNotNull("CommanderPlaysCountWatcher must be installed", watcher);
        return watcher;
    }

    private static CommanderPlaysCountState state(UUID commanderId, int count) {
        return new CommanderPlaysCountState(Collections.singletonList(
                new CommanderPlaysCountState.Count(commanderId, count)
        ));
    }

    private static void expectIllegalArgument(String message, Runnable action) {
        try {
            action.run();
            Assert.fail(message);
        } catch (IllegalArgumentException expected) {
            // expected
        }
    }

    @Test
    public void restoredZeroUsesBaseCostAndRealCommandCastIncrements() {
        addCard(Zone.COMMAND, playerA, ROGRAKH, 1);

        runCode("restore zero", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID id = commanderId(game, player, ROGRAKH);
            CommanderPlaysCountWatcher watcher = watcher(game);
            watcher.restoreStateForGameLoad(state(id, 0), game);
            Assert.assertEquals(0, watcher.getPlaysCount(id));
            Assert.assertEquals(0, watcher.getPlayerCount(player.getId()));
        });

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ROGRAKH);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, ROGRAKH, 1);
        UUID id = commanderId(currentGame, playerA, ROGRAKH);
        Assert.assertEquals(1, watcher(currentGame).getPlaysCount(id));
        Assert.assertEquals(1, watcher(currentGame).getPlayerCount(playerA.getId()));
    }

    @Test
    public void restoredOneAddsTwoGenericManaAndThenIncrements() {
        addCard(Zone.COMMAND, playerA, ROGRAKH, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 2);

        runCode("restore one", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID id = commanderId(game, player, ROGRAKH);
            watcher(game).restoreStateForGameLoad(state(id, 1), game);
        });

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ROGRAKH);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertTappedCount("Wastes", true, 2);
        UUID id = commanderId(currentGame, playerA, ROGRAKH);
        Assert.assertEquals(2, watcher(currentGame).getPlaysCount(id));
        Assert.assertEquals(2, watcher(currentGame).getPlayerCount(playerA.getId()));
    }

    @Test
    public void restoredTwoAddsFourGenericManaAndThenIncrements() {
        addCard(Zone.COMMAND, playerA, ROGRAKH, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 4);

        runCode("restore two", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID id = commanderId(game, player, ROGRAKH);
            watcher(game).restoreStateForGameLoad(state(id, 2), game);
        });

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ROGRAKH);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertTappedCount("Wastes", true, 4);
        UUID id = commanderId(currentGame, playerA, ROGRAKH);
        Assert.assertEquals(3, watcher(currentGame).getPlaysCount(id));
        Assert.assertEquals(3, watcher(currentGame).getPlayerCount(playerA.getId()));
    }

    @Test
    public void partnerCountsRemainIndependentAndPlayerAggregateFeedsNativeConsumers() {
        addCard(Zone.COMMAND, playerA, ROGRAKH, 1);
        addCard(Zone.COMMAND, playerA, JESKA, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 9);

        runCode("restore partner history", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID rograkhId = commanderId(game, player, ROGRAKH);
            UUID jeskaId = commanderId(game, player, JESKA);
            CommanderPlaysCountState restored = new CommanderPlaysCountState(Arrays.asList(
                    new CommanderPlaysCountState.Count(rograkhId, 1),
                    new CommanderPlaysCountState.Count(jeskaId, 2)
            ));
            CommanderPlaysCountWatcher watcher = watcher(game);
            watcher.restoreStateForGameLoad(restored, game);
            Assert.assertEquals(1, watcher.getPlaysCount(rograkhId));
            Assert.assertEquals(2, watcher.getPlaysCount(jeskaId));
            Assert.assertEquals(3, watcher.getPlayerCount(player.getId()));

            Ability sourceAbility = game.getCard(rograkhId).getSpellAbility();
            sourceAbility.setControllerId(player.getId());
            Assert.assertEquals(
                    "CommanderCastCountValue must consume the restored player aggregate",
                    3,
                    CommanderCastCountValue.instance.calculate(game, sourceAbility, null)
            );
        });

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ROGRAKH);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        runCode("after partner A cast", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID rograkhId = commanderId(game, player, ROGRAKH);
            UUID jeskaId = commanderId(game, player, JESKA);
            Assert.assertEquals(2, watcher(game).getPlaysCount(rograkhId));
            Assert.assertEquals(2, watcher(game).getPlaysCount(jeskaId));
            Assert.assertEquals(4, watcher(game).getPlayerCount(player.getId()));
        });

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, JESKA);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        UUID rograkhId = commanderId(currentGame, playerA, ROGRAKH);
        UUID jeskaId = commanderId(currentGame, playerA, JESKA);
        Assert.assertEquals(2, watcher(currentGame).getPlaysCount(rograkhId));
        Assert.assertEquals(3, watcher(currentGame).getPlaysCount(jeskaId));
        Assert.assertEquals(5, watcher(currentGame).getPlayerCount(playerA.getId()));
        assertCounterCount(playerA, JESKA, CounterType.LOYALTY, 5);
    }

    @Test
    public void commanderCastFromHandDoesNotIncrementRestoredCommandZoneHistory() {
        addCard(Zone.COMMAND, playerA, ROGRAKH, 1);

        runCode("restore then move commander to hand", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID id = commanderId(game, player, ROGRAKH);
            CommanderPlaysCountWatcher watcher = watcher(game);
            watcher.restoreStateForGameLoad(state(id, 2), game);
            Card commander = game.getCard(id);
            Assert.assertNotNull(commander);
            Assert.assertTrue(player.moveCardToHandWithInfo(commander, null, game, true));
        });

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ROGRAKH);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        runCode("history unchanged after hand cast", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID id = commanderId(game, player, ROGRAKH);
            Assert.assertEquals(2, watcher(game).getPlaysCount(id));
            Assert.assertEquals(2, watcher(game).getPlayerCount(player.getId()));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void copyRestorePreservesHistoryAndRestoreEmitsNoHistoricalEvents() {
        addCard(Zone.COMMAND, playerA, ROGRAKH, 1);

        runCode("copy restore proof", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            HistoryEventProbe probe = new HistoryEventProbe();
            game.getState().addWatcher(probe);

            UUID id = commanderId(game, player, ROGRAKH);
            CommanderPlaysCountWatcher watcher = watcher(game);
            watcher.restoreStateForGameLoad(state(id, 2), game);

            HistoryEventProbe installedProbe = game.getState().getWatcher(HistoryEventProbe.class);
            Assert.assertNotNull(installedProbe);
            Assert.assertEquals(0, installedProbe.spellCastEvents);
            Assert.assertEquals(0, installedProbe.landPlayedEvents);

            GameState saved = game.getState().copy();
            Assert.assertEquals(2, saved.getWatcher(CommanderPlaysCountWatcher.class).getPlaysCount(id));
            Assert.assertEquals(2, saved.getWatcher(CommanderPlaysCountWatcher.class).getPlayerCount(player.getId()));

            watcher.restoreStateForGameLoad(state(id, 0), game);
            Assert.assertEquals(0, watcher.getPlaysCount(id));

            game.getState().restore(saved);
            CommanderPlaysCountWatcher restoredWatcher = watcher(game);
            Assert.assertEquals(2, restoredWatcher.getPlaysCount(id));
            Assert.assertEquals(2, restoredWatcher.getPlayerCount(player.getId()));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void invalidStateFailsClosed() {
        UUID duplicateId = UUID.randomUUID();
        expectIllegalArgument("negative state must fail", () ->
                new CommanderPlaysCountState.Count(duplicateId, -1));
        expectIllegalArgument("duplicate state must fail", () ->
                new CommanderPlaysCountState(Arrays.asList(
                        new CommanderPlaysCountState.Count(duplicateId, 1),
                        new CommanderPlaysCountState.Count(duplicateId, 2)
                )));

        addCard(Zone.COMMAND, playerA, ROGRAKH, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears", 1);

        runCode("invalid native mappings", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            CommanderPlaysCountWatcher watcher = watcher(game);

            UUID foreignId = UUID.randomUUID();
            expectIllegalArgument("foreign/stale id must fail", () ->
                    watcher.restoreStateForGameLoad(state(foreignId, 1), game));

            Permanent nonCommander = game.getBattlefield().getAllActivePermanents()
                    .stream()
                    .filter(permanent -> "Grizzly Bears".equals(permanent.getName()))
                    .findFirst()
                    .orElseThrow(() -> new AssertionError("Non-commander permanent not found"));
            expectIllegalArgument("non-commander id must fail", () ->
                    watcher.restoreStateForGameLoad(state(nonCommander.getId(), 1), game));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    private static final class HistoryEventProbe extends Watcher {

        private int spellCastEvents;
        private int landPlayedEvents;

        private HistoryEventProbe() {
            super(WatcherScope.GAME);
        }

        @Override
        public void watch(GameEvent event, Game game) {
            if (event.getType() == GameEvent.EventType.SPELL_CAST) {
                spellCastEvents++;
            } else if (event.getType() == GameEvent.EventType.LAND_PLAYED) {
                landPlayedEvents++;
            }
        }
    }
}
