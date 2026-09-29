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
import mage.watchers.common.CommanderInfoWatcher;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;
import java.util.Map;
import java.util.UUID;

/**
 * Discovery probes (4P Commander, turn order A -> D -> C -> B): a player leaves the game
 * while controlling another player's permanents (CR 800.4a).
 */
public class EliminationControlProbe4PTest extends CardTestPlayerAPIImpl {

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

    private Permanent only(String name) {
        Permanent found = null;
        for (Permanent p : currentGame.getBattlefield().getAllActivePermanents()) {
            if (p.getName().equals(name)) {
                Assert.assertNull("single " + name, found);
                found = p;
            }
        }
        return found;
    }

    /** A steals B's creature with Control Magic, then concedes: the creature is B's again. */
    @Test
    public void stolenCreatureReturnsToItsOwnerWhenTheThiefLeaves() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 4);
        addCard(Zone.HAND, playerA, "Control Magic");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Control Magic", "Grizzly Bears");
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        runCode("stolen", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, (info, player, game) ->
                Assert.assertEquals(playerA.getId(), only("Grizzly Bears").getControllerId()));
        concede(2, PhaseStep.PRECOMBAT_MAIN, playerA);
        setStopAt(2, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();

        Assert.assertTrue(playerA.hasLeft());
        Permanent bears = only("Grizzly Bears");
        Assert.assertNotNull("B's creature stays on the battlefield", bears);
        Assert.assertEquals("800.4a: control effects from the leaver end", playerB.getId(), bears.getControllerId());
        Assert.assertNull("the leaver's Aura left the game", only("Control Magic"));
    }

    /** A's Pacifism on B's creature leaves with A: B can attack with it again. */
    @Test
    public void leaversAuraOnAnotherPlayersCreatureLeaves() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.HAND, playerA, "Pacifism");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Pacifism", "Grizzly Bears");
        concede(2, PhaseStep.PRECOMBAT_MAIN, playerA);
        attack(4, playerB, "Grizzly Bears", playerC);
        setStopAt(4, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();

        Assert.assertNull(only("Pacifism"));
        Assert.assertEquals("B's Bears attacked C", 38, playerC.getLife());
    }

    /**
     * A takes B's commander with Threaten and hits C with it: that is combat damage from B's
     * commander to C (903.10a counts the commander, not its controller). Then A leaves; B's
     * commander is B's again.
     */
    @Test
    public void stolenCommanderDealsCommanderDamageAndReturnsWhenTheThiefLeaves() {
        addCard(Zone.COMMAND, playerB, "Isamaru, Hound of Konda", 1);
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 1);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 3);
        addCard(Zone.HAND, playerA, "Threaten");
        castSpell(4, PhaseStep.PRECOMBAT_MAIN, playerB, "Isamaru, Hound of Konda");
        castSpell(5, PhaseStep.PRECOMBAT_MAIN, playerA, "Threaten", "Isamaru, Hound of Konda");
        attack(5, playerA, "Isamaru, Hound of Konda", playerC);
        concede(6, PhaseStep.PRECOMBAT_MAIN, playerA);
        setStopAt(6, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();

        Assert.assertEquals(38, playerC.getLife());
        Permanent isamaru = only("Isamaru, Hound of Konda");
        Assert.assertNotNull(isamaru);
        Assert.assertEquals(playerB.getId(), isamaru.getControllerId());
        CommanderInfoWatcher watcher = currentGame.getState().getWatcher(CommanderInfoWatcher.class,
                isamaru.getMainCard().getId());
        Assert.assertNotNull("B's commander has a watcher", watcher);
        Map<UUID, Integer> damage = watcher.getDamageToPlayer();
        Assert.assertEquals("903.10a: B's commander dealt 2 combat damage to C while A controlled it",
                Integer.valueOf(2), damage.get(playerC.getId()));
    }

    /** A exchanges Gilded Drake for B's creature, then leaves: the creature returns, the Drake leaves. */
    @Test
    public void exchangedControlUnwindsWhenOneSideLeaves() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.HAND, playerA, "Gilded Drake");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Gilded Drake");
        addTarget(playerA, "Grizzly Bears");
        concede(2, PhaseStep.PRECOMBAT_MAIN, playerA);
        setStopAt(2, PhaseStep.POSTCOMBAT_MAIN);
        setStrictChooseMode(true);
        execute();

        Assert.assertEquals(playerB.getId(), only("Grizzly Bears").getControllerId());
        Assert.assertNull("A's Drake left the game with its owner", only("Gilded Drake"));
    }
}
