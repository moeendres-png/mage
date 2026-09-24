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
import org.mage.test.serverside.base.CardTestCommander4Players;

import java.util.Collections;
import java.util.UUID;

/** RG-02 four-player native Commander-damage restore coverage. */
public class RG02CommanderDamageRestore4PTest extends CardTestCommander4Players {

    private static final String ISAMARU = "Isamaru, Hound of Konda";

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
    public void restore21CausesLossIn4PlayerCommander() {
        addCard(Zone.COMMAND, playerA, ISAMARU, 1);

        runCode("restore 21 in 4P", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
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
    }
}
