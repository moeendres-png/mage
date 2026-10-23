package org.mage.test.cards.single.frc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Jace, Multiverse Architect {1}{W}{U}{B}{R} loyalty 4
 * At the beginning of combat on each opponent's turn, they may pay {2}. If they don't, creatures they control can't
 * attack Jaces you control this turn.
 * +1: Draw two cards, then put a card from your hand on the bottom of your library.
 * -3: Exile another target planeswalker or creature you control. Reveal cards from the top of your library until you
 * reveal a creature or planeswalker card. Put that card onto the battlefield and the rest on the bottom of your library
 * in a random order.
 * Jace, Multiverse Architect can be your commander.
 */
public class JaceMultiverseArchitectTest extends CardTestPlayerBase {

    private static final String jace = "Jace, Multiverse Architect";

    @Test
    public void testPlusOneDrawsTwoAndBottomsOne() {
        addCard(Zone.BATTLEFIELD, playerA, jace);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Forest", 3);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "+1: Draw two cards");
        addTarget(playerA, "Forest");
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertCounterCount(playerA, jace, CounterType.LOYALTY, 5);
        assertHandCount(playerA, 1);
        assertLibraryCount(playerA, 2);
    }

    @Test
    public void testMinusThreeReplacesCreature() {
        addCard(Zone.BATTLEFIELD, playerA, jace);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Llanowar Elves");
        addCard(Zone.LIBRARY, playerA, "Forest"); // top, revealed first

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "-3:", "Grizzly Bears");
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertExileCount(playerA, "Grizzly Bears", 1);
        assertPermanentCount(playerA, "Llanowar Elves", 1);
        assertLibraryCount(playerA, 1);
        assertCounterCount(playerA, jace, CounterType.LOYALTY, 1);
    }

    @Test
    public void testOpponentWhoDoesNotPayCannotAttackJace() {
        addCard(Zone.BATTLEFIELD, playerA, jace);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerB, "Island", 2);

        setChoice(playerB, false); // do not pay {2}
        // the restriction lasts until the end of the turn
        runCode("Bears can't attack Jace", 2, PhaseStep.POSTCOMBAT_MAIN, playerB, (info, player, game) -> {
            Permanent bears = getPermanent("Grizzly Bears", playerB);
            Permanent jacePermanent = getPermanent(jace, playerA);
            Assert.assertFalse(info, bears.canAttackInPrinciple(jacePermanent.getId(), game));
            Assert.assertTrue("the player stays attackable", bears.canAttackInPrinciple(playerA.getId(), game));
        });
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertCounterCount(playerA, jace, CounterType.LOYALTY, 4);
    }

    @Test
    public void testOpponentWhoPaysMayAttackJace() {
        addCard(Zone.BATTLEFIELD, playerA, jace);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerB, "Island", 2);

        setChoice(playerB, true); // pay {2}
        attack(2, playerB, "Grizzly Bears", jace);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertCounterCount(playerA, jace, CounterType.LOYALTY, 2);
    }

    @Test
    public void testOpponentWhoDoesNotPayMayStillAttackThePlayer() {
        addCard(Zone.BATTLEFIELD, playerA, jace);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        setChoice(playerB, false); // cannot pay anyway
        attack(2, playerB, "Grizzly Bears", playerA);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.END_TURN);
        execute();

        assertLife(playerA, 18);
    }
}
