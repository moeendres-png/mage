package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * The Foretold Soldier {2}{G}{G} 6/6
 * This creature must be blocked if able.
 * This creature can't be blocked by more than one creature.
 * Whenever this creature deals damage, exile it face down. It becomes foretold.
 * Foretell {1}{G}
 */
public class TheForetoldSoldierTest extends CardTestPlayerBase {

    private static final String soldier = "The Foretold Soldier";

    @Test
    public void testDamageExilesItForetoldAndItIsCastForTheForetellCostLater() {
        addCard(Zone.BATTLEFIELD, playerA, soldier);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2); // the foretell cost {1}{G}, not the mana cost {2}{G}{G}

        attack(1, playerA, soldier);
        activateAbility(3, PhaseStep.PRECOMBAT_MAIN, playerA, "Foretell {1}{G}");
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.BEGIN_COMBAT);
        execute();

        assertLife(playerB, 20 - 6);
        assertPermanentCount(playerA, soldier, 1); // exiled after the first combat, cast again on turn 3
        assertTappedCount("Forest", true, 2);
    }

    @Test
    public void testItIsInExileFaceDownBeforeTheLaterTurn() {
        addCard(Zone.BATTLEFIELD, playerA, soldier);

        attack(1, playerA, soldier);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 6);
        assertExileCount(playerA, soldier, 1);
        assertPermanentCount(playerA, soldier, 0);
    }

    @Test
    public void testItCannotBeCastForTheForetellCostOnTheTurnItWasExiled() {
        addCard(Zone.BATTLEFIELD, playerA, soldier);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);

        attack(1, playerA, soldier);
        checkPlayableAbility("not on the same turn", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Foretell {1}{G}", false);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void testAtMostOneCreatureCanBlockIt() {
        addCard(Zone.BATTLEFIELD, playerA, soldier);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", 2);

        attack(1, playerA, soldier);
        block(1, playerB, "Grizzly Bears:0", soldier); // the one block that is required
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20); // blocked, no damage to the player
        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertPermanentCount(playerB, "Grizzly Bears", 1); // the second one was not needed
    }
}
