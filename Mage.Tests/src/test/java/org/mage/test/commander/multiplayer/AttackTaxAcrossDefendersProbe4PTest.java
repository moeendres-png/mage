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
 * Discovery probe (4P Commander, live pin): Propaganda ("Creatures can't attack you unless their
 * controller pays {2} for each creature they control that's attacking you.") controlled by B taxes
 * only the attacker aimed at B, not A's attacker aimed at C.
 */
public class AttackTaxAcrossDefendersProbe4PTest extends CardTestPlayerAPIImpl {

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

    /** A has exactly {2}: enough for the one creature attacking B, while the other attacks C for free. */
    @Test
    public void onlyTheAttackerOfTheTaxingPlayerPays() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Raging Goblin");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerB, "Propaganda");
        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Raging Goblin", playerC);
        setChoice(playerA, true); // pay {2}
        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(false);
        execute();
        assertLife(playerB, 40 - 2);
        assertLife(playerC, 40 - 1);
        assertTappedCount("Plains", true, 2);
    }

    /** With no mana, the creature attacking C still attacks; only the attack on B is impossible. */
    @Test
    public void attackOnAnotherPlayerNeedsNoPayment() {
        addCard(Zone.BATTLEFIELD, playerA, "Raging Goblin");
        addCard(Zone.BATTLEFIELD, playerB, "Propaganda");
        attack(1, playerA, "Raging Goblin", playerC);
        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();
        assertLife(playerC, 40 - 1);
    }
}
