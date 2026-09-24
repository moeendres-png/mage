package org.mage.test.serverside.rg02;

import mage.cards.Card;
import mage.constants.CommanderCardType;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.Game;
import mage.players.Player;
import mage.watchers.common.CommanderInfoWatcher;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommander3PlayersFFA;

import java.util.LinkedHashMap;
import java.util.Map;
import java.util.UUID;

/**
 * RG-02 native Commander-damage state-restore qualification.
 *
 * The tests deliberately restore the native CommanderInfoWatcher ledger rather
 * than replaying synthetic historical damage events. Post-restore behavior is
 * then driven by ordinary engine combat/SBA processing.
 */
public class RG02CommanderDamageRestoreTest extends CardTestCommander3PlayersFFA {

    private static final String ISAMARU = "Isamaru, Hound of Konda";
    private static final String ROGRAKH = "Rograkh, Son of Rohgahh";
    private static final String JESKA = "Jeska, Thrice Reborn";

    private static UUID commanderId(Game game, Player player, String name) {
        Player currentPlayer = game.getPlayer(player.getId());
        Assert.assertNotNull("Current native player must exist", currentPlayer);
        return game.getCommandersIds(currentPlayer, CommanderCardType.ANY, false)
                .stream()
                .filter(id -> {
                    Card card = game.getCard(id);
                    return card != null && name.equals(card.getName());
                })
                .findFirst()
                .orElseThrow(() -> new AssertionError("Commander not found: " + name));
    }

    private static CommanderInfoWatcher watcher(Game game, Player owner, String commanderName) {
        UUID id = commanderId(game, owner, commanderName);
        CommanderInfoWatcher watcher = game.getState().getWatcher(CommanderInfoWatcher.class, id);
        Assert.assertNotNull("CommanderInfoWatcher must be installed for " + commanderName, watcher);
        return watcher;
    }

    private static void restore(Game game, Player owner, String commanderName, Player damagedPlayer, int amount) {
        Map<UUID, Integer> state = new LinkedHashMap<>();
        state.put(damagedPlayer.getId(), amount);
        watcher(game, owner, commanderName).restoreDamageStateForGameLoad(state, game);
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
    public void restore20DoesNotLoseIn3PlayerGame() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);

        runCode("restore 20", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                restore(game, player, ISAMARU, playerB, 20));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        Assert.assertNotNull("20 Commander damage must not eliminate the player",
                currentGame.getPlayer(playerB.getId()));
        assertLife(playerB, 40);
    }

    @Test
    public void restore21CausesStateBasedLossAndLaterChecksRemainStable() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);

        runCode("restore 21", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                restore(game, player, ISAMARU, playerB, 21));

        // Keep the three-player game running after B loses so later SBA checks occur.
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLostTheGame(playerB);
        Assert.assertNotNull("Remaining player must still be in the multiplayer game",
                currentGame.getPlayer(playerC.getId()));
    }

    @Test
    public void damageFromDifferentCommandersDoesNotAggregate() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);
        addCard(Zone.COMMAND, playerC, "Norin the Wary", 1);

        runCode("restore split commander damage", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            restore(game, playerA, ISAMARU, playerB, 11);
            restore(game, playerC, "Norin the Wary", playerB, 10);
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        Assert.assertNotNull("11 + 10 from different commanders must not aggregate",
                currentGame.getPlayer(playerB.getId()));
    }

    @Test
    public void partnerCommandersHaveIndependentDamageLedgers() {
        addCard(Zone.COMMAND, playerA, ROGRAKH, 1);
        addCard(Zone.COMMAND, playerA, JESKA, 1);

        runCode("restore independent partner damage", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            restore(game, player, ROGRAKH, playerB, 11);
            restore(game, player, JESKA, playerB, 10);
            Assert.assertEquals(Integer.valueOf(11),
                    watcher(game, player, ROGRAKH).getDamageToPlayer().get(playerB.getId()));
            Assert.assertEquals(Integer.valueOf(10),
                    watcher(game, player, JESKA).getDamageToPlayer().get(playerB.getId()));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        Assert.assertNotNull("Partner commander damage must remain independent",
                currentGame.getPlayer(playerB.getId()));
    }

    @Test
    public void restored19ThenRealCommanderCombatDamageReachesThreshold() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 1);

        runCode("restore 19", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                restore(game, player, ISAMARU, playerB, 19));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ISAMARU);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        attack(4, playerA, ISAMARU, playerB);

        setStopAt(4, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLostTheGame(playerB);
    }

    @Test
    public void noncombatCommanderDamageDoesNotIncrementLedger() {
        String ruric = "Ruric Thar, the Unbowed";
        addCard(Zone.COMMAND, playerA, ruric, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 5);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Mountain", 1);
        addCard(Zone.HAND, playerB, "Shock", 1);

        runCode("restore 20", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                restore(game, player, ruric, playerB, 20));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ruric);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);

        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerB, "Shock", playerC);
        waitStackResolved(3, PhaseStep.PRECOMBAT_MAIN, playerB);
        runCode("verify noncombat ignored", 3, PhaseStep.PRECOMBAT_MAIN, playerB, (info, player, game) ->
                Assert.assertEquals(Integer.valueOf(20),
                        watcher(game, playerA, ruric).getDamageToPlayer().get(playerB.getId())));

        setStopAt(3, PhaseStep.BEGIN_COMBAT);
        execute();

        Assert.assertNotNull("Noncombat damage from a commander must not cause commander-damage loss",
                currentGame.getPlayer(playerB.getId()));
        assertLife(playerB, 34);
    }

    @Test
    public void commanderDamageTracksIdentityAfterControllerChange() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Mountain", 3);
        addCard(Zone.HAND, playerB, "Act of Treason", 1);

        runCode("restore 19", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                restore(game, player, ISAMARU, playerC, 19));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ISAMARU);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);

        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerB, "Act of Treason", ISAMARU);
        waitStackResolved(3, PhaseStep.PRECOMBAT_MAIN, playerB);
        attack(3, playerB, ISAMARU, playerC);

        setStopAt(3, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLostTheGame(playerC);
    }

    @Test
    public void commanderDamageContinuesAfterBlinkReentry() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.HAND, playerA, "Cloudshift", 1);

        runCode("restore 17", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                restore(game, player, ISAMARU, playerB, 17));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ISAMARU);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);

        attack(4, playerA, ISAMARU, playerB);
        castSpell(4, PhaseStep.POSTCOMBAT_MAIN, playerA, "Cloudshift", ISAMARU);
        waitStackResolved(4, PhaseStep.POSTCOMBAT_MAIN, playerA);

        attack(7, playerA, ISAMARU, playerB);

        setStopAt(7, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLostTheGame(playerB);
    }

    @Test
    public void modalDoubleFacedCommanderUsesFrontIdentityForDamage() {
        String esika = "Esika, God of the Tree";
        addCard(Zone.COMMAND, playerA, esika, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 3);

        runCode("restore 20", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                restore(game, player, esika, playerB, 20));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, esika);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);
        attack(4, playerA, esika, playerB);

        setStopAt(4, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLostTheGame(playerB);
    }

    @Test
    public void mutatedPermanentNormalizesCommanderSourceIdentity() {
        String otrimi = "Otrimi, the Ever-Playful";
        String host = "Beastcaller Savant";
        addCard(Zone.COMMAND, playerA, otrimi, 1);
        addCard(Zone.BATTLEFIELD, playerA, host, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);

        runCode("restore 20", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                restore(game, player, otrimi, playerB, 20));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, otrimi + " using Mutate", host);
        setChoice(playerA, true);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN, playerA);

        attack(4, playerA, host, playerB);

        setStopAt(4, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertLostTheGame(playerB);
    }

    @Test
    public void invalidRestorePayloadsFailBeforeMutation() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);

        runCode("validate restore payloads", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            CommanderInfoWatcher watcher = watcher(game, player, ISAMARU);

            Map<UUID, Integer> baseline = new LinkedHashMap<>();
            baseline.put(playerB.getId(), 7);
            watcher.restoreDamageStateForGameLoad(baseline, game);
            Assert.assertEquals(Integer.valueOf(7), watcher.getDamageToPlayer().get(playerB.getId()));

            Map<UUID, Integer> unknownPlayer = new LinkedHashMap<>();
            unknownPlayer.put(playerB.getId(), 9);
            unknownPlayer.put(UUID.randomUUID(), 1);
            expectIllegalArgument("Unknown player id must be rejected",
                    () -> watcher.restoreDamageStateForGameLoad(unknownPlayer, game));
            Assert.assertEquals("Unknown-player failure must not partially mutate",
                    Integer.valueOf(7), watcher.getDamageToPlayer().get(playerB.getId()));

            Map<UUID, Integer> negative = new LinkedHashMap<>();
            negative.put(playerB.getId(), -1);
            expectIllegalArgument("Negative amount must be rejected",
                    () -> watcher.restoreDamageStateForGameLoad(negative, game));
            Assert.assertEquals("Negative failure must not partially mutate",
                    Integer.valueOf(7), watcher.getDamageToPlayer().get(playerB.getId()));

            Map<UUID, Integer> nullAmount = new LinkedHashMap<>();
            nullAmount.put(playerB.getId(), null);
            expectIllegalArgument("Null amount must be rejected",
                    () -> watcher.restoreDamageStateForGameLoad(nullAmount, game));
            Assert.assertEquals("Null-amount failure must not partially mutate",
                    Integer.valueOf(7), watcher.getDamageToPlayer().get(playerB.getId()));

            Map<UUID, Integer> nullPlayer = new LinkedHashMap<>();
            nullPlayer.put(null, 1);
            expectIllegalArgument("Null player id must be rejected",
                    () -> watcher.restoreDamageStateForGameLoad(nullPlayer, game));
            Assert.assertEquals("Null-player failure must not partially mutate",
                    Integer.valueOf(7), watcher.getDamageToPlayer().get(playerB.getId()));

            expectIllegalArgument("Null payload must be rejected",
                    () -> watcher.restoreDamageStateForGameLoad(null, game));
            expectIllegalArgument("Null game must be rejected",
                    () -> watcher.restoreDamageStateForGameLoad(baseline, null));
            Assert.assertEquals("Null-input failures must not partially mutate",
                    Integer.valueOf(7), watcher.getDamageToPlayer().get(playerB.getId()));
        });

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
