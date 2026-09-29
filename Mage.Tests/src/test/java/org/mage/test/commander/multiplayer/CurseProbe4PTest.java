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
 * Discovery probe (4P Commander, turn order A -> D -> C -> B, live pin): Curse of Opulence
 * ("Enchant player / Whenever enchanted player is attacked, create a Gold token. Each opponent
 * attacking that player does the same.") cast by A on C.
 */
public class CurseProbe4PTest extends CardTestPlayerAPIImpl {

    private static final String CURSE = "Curse of Opulence";

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

    private void curseC() {
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 1);
        addCard(Zone.HAND, playerA, CURSE);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, CURSE, playerC);
    }

    /** D (an opponent of C, not the curse's controller) attacks C: A and D each get a Gold. */
    @Test
    public void attackerOfTheEnchantedPlayerAndCurseControllerEachGetGold() {
        curseC();
        addCard(Zone.BATTLEFIELD, playerD, "Grizzly Bears");
        attack(2, playerD, "Grizzly Bears", playerC);
        setStopAt(2, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();
        assertPermanentCount(playerA, "Gold Token", 1);
        assertPermanentCount(playerD, "Gold Token", 1);
        assertPermanentCount(playerC, "Gold Token", 0);
    }

    /** D attacks B (not enchanted): no Gold at all. */
    @Test
    public void attackOnAnotherPlayerDoesNotTrigger() {
        curseC();
        addCard(Zone.BATTLEFIELD, playerD, "Grizzly Bears");
        attack(2, playerD, "Grizzly Bears", playerB);
        setStopAt(2, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();
        assertPermanentCount(playerA, "Gold Token", 0);
        assertPermanentCount(playerD, "Gold Token", 0);
    }

    /** The enchanted player leaves: the curse goes to A's graveyard (state-based action). */
    @Test
    public void curseOnAPlayerWhoLeftGoesToTheGraveyard() {
        curseC();
        concede(2, PhaseStep.PRECOMBAT_MAIN, playerC);
        setStopAt(2, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();
        assertPermanentCount(playerA, CURSE, 0);
        assertGraveyardCount(playerA, CURSE, 1);
    }
}
