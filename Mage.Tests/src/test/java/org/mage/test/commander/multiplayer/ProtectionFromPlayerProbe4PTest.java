package org.mage.test.commander.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import org.junit.Test;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * Discovery probe (4P Commander, turn order A -> D -> C -> B): True-Name Nemesis ("As True-Name
 * Nemesis enters, choose a player. True-Name Nemesis has protection from the chosen player.")
 * protects only from the chosen player, not from every opponent.
 */
public class ProtectionFromPlayerProbe4PTest extends CardTestPlayerAPIImpl {

    private static final String TNN = "True-Name Nemesis";

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new CommanderFreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 40, 7);
        playerA = createPlayer(game, "PlayerA");
        playerB = createPlayer(game, "PlayerB");
        playerC = createPlayer(game, "PlayerC");
        playerD = createPlayer(game, "PlayerD");
        return game;
    }

    private void nemesisChoosing(String chosen) {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 3);
        addCard(Zone.HAND, playerA, TNN);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, TNN);
        setChoice(playerA, chosen);
    }

    /** The chosen player's sweeper damage is prevented. */
    @Test
    public void chosenPlayersDamageIsPrevented() {
        nemesisChoosing("PlayerC");
        addCard(Zone.BATTLEFIELD, playerC, "Mountain", 2);
        addCard(Zone.HAND, playerC, "Pyroclasm");
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerC, "Pyroclasm");
        setStopAt(3, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();
        assertPermanentCount(playerA, TNN, 1);
    }

    /** Another opponent's sweeper still kills it. */
    @Test
    public void otherOpponentsDamageIsNotPrevented() {
        nemesisChoosing("PlayerC");
        addCard(Zone.BATTLEFIELD, playerD, "Mountain", 2);
        addCard(Zone.HAND, playerD, "Pyroclasm");
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerD, "Pyroclasm");
        setStopAt(2, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();
        assertPermanentCount(playerA, TNN, 0);
    }

    /** Another opponent may target it. */
    @Test
    public void otherOpponentMayTargetIt() {
        nemesisChoosing("PlayerC");
        addCard(Zone.BATTLEFIELD, playerB, "Mountain", 1);
        addCard(Zone.HAND, playerB, "Lightning Bolt");
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerB, "Lightning Bolt", TNN);
        setStopAt(1, PhaseStep.END_TURN);
        setStrictChooseMode(true);
        execute();
        assertPermanentCount(playerA, TNN, 0);
    }

    /** Another opponent's creature may block it; the chosen player's creature may not. */
    @Test
    public void onlyTheChosenPlayersCreaturesCantBlock() {
        nemesisChoosing("PlayerC");
        addCard(Zone.BATTLEFIELD, playerC, "Grizzly Bears");
        attack(5, playerA, TNN, playerC);
        setStopAt(5, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();
        assertLife(playerC, 40 - 3);
        assertPermanentCount(playerC, "Grizzly Bears", 1);
    }

    /** Even when C tries to block, its creature can't block the Nemesis. */
    @Test
    public void chosenPlayersCreatureCantBlock() {
        nemesisChoosing("PlayerC");
        addCard(Zone.BATTLEFIELD, playerC, "Grizzly Bears");
        attack(5, playerA, TNN, playerC);
        block(5, playerC, "Grizzly Bears", TNN);
        setStopAt(5, PhaseStep.END_COMBAT);
        setStrictChooseMode(false);
        execute();
        assertLife(playerC, 40 - 3);
        assertPermanentCount(playerC, "Grizzly Bears", 1);
        assertPermanentCount(playerA, TNN, 1);
    }

    /** Another opponent's creature may block it when it attacks that opponent. */
    @Test
    public void otherOpponentsCreatureMayBlock() {
        nemesisChoosing("PlayerC");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        attack(5, playerA, TNN, playerB);
        block(5, playerB, "Grizzly Bears", TNN);
        setStopAt(5, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();
        assertLife(playerB, 40);
        assertPermanentCount(playerA, TNN, 0);
    }
}
