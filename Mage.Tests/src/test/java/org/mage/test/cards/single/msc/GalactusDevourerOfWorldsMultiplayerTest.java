package org.mage.test.cards.single.msc;

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
 * Insatiable Hunger in a four-player game: "Galactus attacks an opponent with the most life
 * among your opponents each combat if able". No attack command is given in these tests, so
 * every attack below is forced by the requirement (Combat.checkAttackRequirements with
 * RequirementEffect.mustAttackDefenders).
 *
 * @author commander-lab
 */
public class GalactusDevourerOfWorldsMultiplayerTest extends CardTestPlayerAPIImpl {

    private static final String GALACTUS = "Galactus, Devourer of Worlds";

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

    @Test
    public void testAttacksTheOpponentWithTheMostLife() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, GALACTUS);
        setLife(playerB, 15);
        setLife(playerC, 25);
        setLife(playerD, 10);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        // fails if the requirement is missing (no attack) or picks another defender
        assertLife(playerC, 25 - 12);
        assertLife(playerB, 15);
        assertLife(playerD, 10);
    }

    @Test
    public void testTieForMostLifeLetsTheControllerChooseAmongTheTied() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, GALACTUS);
        setLife(playerB, 25);
        setLife(playerC, 25);
        setLife(playerD, 10);

        // two defenders satisfy the requirement: the controller chooses one of them
        addTarget(playerA, playerB);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 25 - 12);
        assertLife(playerC, 25);
        assertLife(playerD, 10);
    }

    @Test
    public void testNoRequirementWithSilverSurfer() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, GALACTUS);
        addCard(Zone.BATTLEFIELD, playerA, "Silver Surfer, Galactus's Herald");
        setLife(playerC, 25);

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        // control: without Silver Surfer the first test shows Galactus is able to attack here
        assertLife(playerB, 20);
        assertLife(playerC, 25);
        assertLife(playerD, 20);
    }

    @Test(expected = AssertionError.class)
    public void testLowerLifeOpponentIsNotAChoice() {
        // same tie as above: PlayerD (10 life) is not among the defenders Galactus must attack,
        // so naming it leaves the forced-attack choice unanswered and strict mode fails.
        // Without the multi-defender requirement every opponent would be a legal choice.
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, GALACTUS);
        setLife(playerB, 25);
        setLife(playerC, 25);
        setLife(playerD, 10);

        addTarget(playerA, playerD);

        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }
}
