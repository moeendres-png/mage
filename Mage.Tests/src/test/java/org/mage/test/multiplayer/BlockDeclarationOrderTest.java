package org.mage.test.multiplayer;

import mage.abilities.Ability;
import mage.constants.PhaseStep;
import mage.constants.RangeOfInfluence;
import mage.constants.Zone;
import mage.game.Game;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestComputerPlayer;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestCommander4Players;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.UUID;

/**
 * F-29: rule 802.4 — "If more than one player is being attacked ..., each defending player in APNAP order
 * declares blockers as the declare blockers step begins. The first defending player declares all their
 * blocks, then the second defending player, and so on."
 * <p>
 * Combat.selectBlockers iterated getPlayerDefenders, a hash set of player ids, so the declaration order was
 * arbitrary and differed between otherwise identical games. Four players, turn order A -> D -> C -> B; each
 * active player attacks all three opponents, and a recording player logs who declares blockers, in order.
 */
public class BlockDeclarationOrderTest extends CardTestCommander4Players {

    private final List<String> declarations = new ArrayList<>();

    @Override
    protected TestPlayer createNewPlayer(String playerName, RangeOfInfluence rangeOfInfluence) {
        return new RecordingPlayer(new TestComputerPlayer(playerName, rangeOfInfluence), this);
    }

    private void everyoneHasCreatures() {
        for (TestPlayer player : Arrays.asList(playerA, playerB, playerC, playerD)) {
            addCard(Zone.BATTLEFIELD, player, "Grizzly Bears", 1);
            addCard(Zone.BATTLEFIELD, player, "Hill Giant", 1);
            addCard(Zone.BATTLEFIELD, player, "Craw Wurm", 1);
            addCard(Zone.BATTLEFIELD, player, "Wall of Stone", 1);
        }
    }

    @Test
    public void defendersDeclareInApnapOrderOnAsTurn() {
        everyoneHasCreatures();
        attack(1, playerA, "Grizzly Bears", playerB);
        attack(1, playerA, "Hill Giant", playerC);
        attack(1, playerA, "Craw Wurm", playerD);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();
        Assert.assertEquals(Arrays.asList("PlayerD", "PlayerC", "PlayerB"), declarations);
    }

    @Test
    public void defendersDeclareInApnapOrderOnDsTurn() {
        everyoneHasCreatures();
        attack(2, playerD, "Grizzly Bears", playerA);
        attack(2, playerD, "Hill Giant", playerB);
        attack(2, playerD, "Craw Wurm", playerC);
        setStopAt(2, PhaseStep.END_COMBAT);
        execute();
        Assert.assertEquals(Arrays.asList("PlayerC", "PlayerB", "PlayerA"), declarations);
    }

    @Test
    public void defendersDeclareInApnapOrderOnCsTurn() {
        everyoneHasCreatures();
        attack(3, playerC, "Grizzly Bears", playerD);
        attack(3, playerC, "Hill Giant", playerA);
        attack(3, playerC, "Craw Wurm", playerB);
        setStopAt(3, PhaseStep.END_COMBAT);
        execute();
        Assert.assertEquals(Arrays.asList("PlayerB", "PlayerA", "PlayerD"), declarations);
    }

    /** Records which player declares blockers, in order. */
    static final class RecordingPlayer extends TestPlayer {

        private final transient BlockDeclarationOrderTest test;

        RecordingPlayer(TestComputerPlayer computerPlayer, BlockDeclarationOrderTest test) {
            super(computerPlayer);
            this.test = test;
        }

        private RecordingPlayer(RecordingPlayer player) {
            super(player);
            this.test = player.test;
        }

        @Override
        public void selectBlockers(Ability source, Game game, UUID defendingPlayerId) {
            test.declarations.add(getName());
            super.selectBlockers(source, game, defendingPlayerId);
        }

        @Override
        public RecordingPlayer copy() {
            return new RecordingPlayer(this);
        }
    }
}
