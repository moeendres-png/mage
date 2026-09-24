package org.mage.test.serverside.rg02;

import mage.cards.Card;
import mage.constants.CommanderCardType;
import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.players.Player;
import mage.watchers.common.CommanderInfoWatcher;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.Collections;
import java.util.UUID;

/** RG-02 five-player native Commander-damage restore coverage. */
public class RG02CommanderDamageRestore5PTest extends CardTestPlayerAPIImpl {

    private static final String ISAMARU = "Isamaru, Hound of Konda";
    private TestPlayer playerE;

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new CommanderFreeForAll(
                MultiplayerAttackOption.MULTIPLE,
                RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0),
                40,
                7);
        playerA = createPlayer(game, "PlayerA", "CommanderDuel.dck");
        playerB = createPlayer(game, "PlayerB", "CommanderDuel.dck");
        playerC = createPlayer(game, "PlayerC", "CommanderDuel.dck");
        playerD = createPlayer(game, "PlayerD", "CommanderDuel.dck");
        playerE = createPlayer(game, "PlayerE", "CommanderDuel.dck");
        return game;
    }

    private static UUID commanderId(Game game, Player owner) {
        return game.getCommandersIds(game.getPlayer(owner.getId()), CommanderCardType.ANY, false)
                .stream()
                .filter(id -> {
                    Card card = game.getCard(id);
                    return card != null && ISAMARU.equals(card.getName());
                })
                .findFirst()
                .orElseThrow(() -> new AssertionError("Commander not found: " + ISAMARU));
    }

    @Test
    public void restore21CausesLossIn5PlayerCommander() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);

        runCode("restore 21 in 5P", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            UUID id = commanderId(game, player);
            CommanderInfoWatcher watcher = game.getState().getWatcher(CommanderInfoWatcher.class, id);
            Assert.assertNotNull(watcher);
            watcher.restoreDamageStateForGameLoad(
                    Collections.singletonMap(playerB.getId(), 21), game);
        });

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLostTheGame(playerB);
        Assert.assertNotNull(currentGame.getPlayer(playerC.getId()));
        Assert.assertNotNull(currentGame.getPlayer(playerD.getId()));
        Assert.assertNotNull(currentGame.getPlayer(playerE.getId()));
    }
}
