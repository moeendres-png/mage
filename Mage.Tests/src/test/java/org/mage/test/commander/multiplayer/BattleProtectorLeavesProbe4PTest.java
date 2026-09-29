package org.mage.test.commander.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.CommanderFreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * Discovery probe (4P Commander, turn order A -> D -> C -> B): a battle's protector leaves the
 * game. A battle whose protector is no longer in the game gets a new protector chosen by its
 * controller (state-based action), so it can still be attacked.
 */
public class BattleProtectorLeavesProbe4PTest extends CardTestPlayerAPIImpl {

    private static final String SIEGE = "Invasion of Zendikar";

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

    private Permanent siege() {
        return currentGame.getBattlefield().getAllActivePermanents().stream()
                .filter(p -> p.getName().equals(SIEGE)).findFirst().orElse(null);
    }

    /** Control: without the concession, C (not the protector) attacks the battle protected by D. */
    @Test
    public void controlNonProtectorAttacksTheBattle() {
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 4);
        addCard(Zone.HAND, playerA, SIEGE);
        addCard(Zone.BATTLEFIELD, playerC, "Grizzly Bears");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, SIEGE);
        setChoice(playerA, "PlayerD"); // protector
        attack(3, playerC, "Grizzly Bears", SIEGE);
        setStopAt(3, PhaseStep.END_COMBAT);
        setStrictChooseMode(false);
        execute();

        Assert.assertEquals(1, siege().getCounters(currentGame).getCount(mage.counters.CounterType.DEFENSE));
    }

    /** C, still an opponent of A, attacks the battle after its protector D left. */
    @Test
    public void battleIsStillAttackableAfterItsProtectorLeft() {
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 4);
        addCard(Zone.HAND, playerA, SIEGE);
        addCard(Zone.BATTLEFIELD, playerC, "Grizzly Bears");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, SIEGE);
        setChoice(playerA, "PlayerD"); // protector
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        concede(2, PhaseStep.PRECOMBAT_MAIN, playerD);
        attack(3, playerC, "Grizzly Bears", SIEGE);
        setStopAt(3, PhaseStep.END_COMBAT);
        setStrictChooseMode(false);
        execute();

        Assert.assertEquals("Grizzly Bears dealt 2 damage to the battle (defense 3 -> 1)", 1,
                siege().getCounters(currentGame).getCount(mage.counters.CounterType.DEFENSE));
    }

    @Test
    public void protectorLeavesAndTheBattleGetsANewProtector() {
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 4);
        addCard(Zone.HAND, playerA, SIEGE);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, SIEGE);
        setChoice(playerA, "PlayerD"); // protector
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        runCode("protector D", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, (info, player, game) ->
                Assert.assertEquals(playerD.getId(), siege().getProtectorId()));
        concede(2, PhaseStep.PRECOMBAT_MAIN, playerD);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        setStrictChooseMode(false);
        execute();

        Assert.assertTrue(playerD.hasLeft());
        Permanent battle = siege();
        Assert.assertNotNull("the battle stays", battle);
        Assert.assertNotEquals("a player who left the game can't protect a battle", playerD.getId(),
                battle.getProtectorId());
        Assert.assertTrue("the new protector is an opponent of A still in the game",
                battle.getProtectorId() != null
                        && (battle.getProtectorId().equals(playerB.getId()) || battle.getProtectorId().equals(playerC.getId())));
    }
}
