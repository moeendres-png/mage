package org.mage.test.multiplayer;

import mage.constants.MultiplayerAttackOption;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.FreeForAll;
import mage.game.Game;
import mage.game.GameException;
import mage.game.mulligan.MulliganType;
import org.junit.Test;
import org.mage.test.serverside.base.impl.CardTestPlayerAPIImpl;

import java.io.FileNotFoundException;

/**
 * F-28: a "blocks this turn if able" requirement in multiplayer (rules 509.1c, 802.4a).
 * <p>
 * A defending player's creature can block only creatures attacking that player, a planeswalker that
 * player controls, or a battle that player protects (802.4a). Combat.checkBlockRequirementsAfter
 * decided "this creature could block" with Permanent.canBlock alone, which checks only that the
 * attacker is an opponent's. A forced blocker whose only candidate attacker was attacking another
 * player was therefore required to block, a block the engine itself rejects (CombatGroup.canBlock),
 * so block declaration never became valid: a human (external) controller was re-asked forever, the
 * AI path gave up with "AI can't find good blocker combination".
 * <p>
 * Players are created A..D; turn order is A, D, C, B.
 */
public class ForcedBlockOtherDefenderTest extends CardTestPlayerAPIImpl {

    @Override
    protected Game createNewGameAndPlayers() throws GameException, FileNotFoundException {
        Game game = new FreeForAll(MultiplayerAttackOption.MULTIPLE, RangeOfInfluence.ALL,
                MulliganType.GAME_DEFAULT.getMulligan(0), 20, 7);
        playerA = createPlayer(game, "PlayerA");
        playerB = createPlayer(game, "PlayerB");
        playerC = createPlayer(game, "PlayerC");
        playerD = createPlayer(game, "PlayerD");
        return game;
    }

    /**
     * C's Hill Giant must block if able, but it can block neither the Bears (attacking B) nor the
     * flying Air Elemental (attacking C): the requirement imposes nothing and combat proceeds.
     */
    @Test
    public void forcedBlockerCannotBeRequiredToBlockACreatureAttackingAnotherPlayer() {
        addCard(Zone.HAND, playerA, "Culling Mark"); // {2}{G} Sorcery: Target creature blocks this turn if able.
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerA, "Air Elemental"); // 4/4 flying
        addCard(Zone.BATTLEFIELD, playerC, "Hill Giant"); // 3/3

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Culling Mark", "Hill Giant");
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Air Elemental", playerC);

        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();

        assertLife(playerB, 20 - 2);
        assertLife(playerC, 20 - 4);
        assertLife(playerD, 20);
        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertPermanentCount(playerC, "Hill Giant", 1);
    }

    /**
     * Control: when a creature attacks the forced blocker's controller and can be blocked, the
     * requirement still applies — C's Hill Giant must block the Bears attacking C (the AI path
     * declares the required block).
     */
    @Test
    public void forcedBlockerStillBlocksACreatureAttackingItsController() {
        addCard(Zone.HAND, playerA, "Culling Mark");
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Air Elemental");
        addCard(Zone.BATTLEFIELD, playerC, "Hill Giant");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Culling Mark", "Hill Giant");
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        attack(1, playerA, "Air Elemental", playerB);
        attack(1, playerA, "Grizzly Bears", playerC);

        setStopAt(1, PhaseStep.END_COMBAT);
        setStrictChooseMode(true);
        execute();

        assertLife(playerB, 20 - 4);
        assertLife(playerC, 20);
        assertPermanentCount(playerA, "Grizzly Bears", 0); // blocked by the 3/3 Giant and died
        assertGraveyardCount(playerA, "Grizzly Bears", 1);
    }
}
