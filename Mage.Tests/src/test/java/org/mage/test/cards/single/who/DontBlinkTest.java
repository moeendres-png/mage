package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Don't Blink {1}{U}
 * Instant
 * Until end of turn, if one or more creatures would enter from exile or after being cast from exile,
 * their owners shuffle them into their libraries instead.
 * Cycling {2}
 */
public class DontBlinkTest extends CardTestPlayerBase {

    private static final String dontBlink = "Don't Blink";
    private static final String cloudshift = "Cloudshift"; // {W} instant: exile target creature you control, then return it
    private static final String bears = "Grizzly Bears";

    @Test
    public void testAFlickeredCreatureIsShuffledIntoItsOwnersLibrary() {
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.HAND, playerA, dontBlink);
        addCard(Zone.HAND, playerA, cloudshift);
        addCard(Zone.BATTLEFIELD, playerA, bears);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, dontBlink);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, cloudshift, bears);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, bears, 0);
        assertExileCount(playerA, bears, 0);
        assertGraveyardCount(playerA, bears, 0);
        assertLibraryCount(playerA, bears, 1);
    }

    @Test
    public void testWithoutItTheCreatureReturns() {
        addCard(Zone.BATTLEFIELD, playerA, "Plains");
        addCard(Zone.HAND, playerA, cloudshift);
        addCard(Zone.BATTLEFIELD, playerA, bears);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, cloudshift, bears);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, bears, 1);
        assertLibraryCount(playerA, bears, 0);
    }

    @Test
    public void testItLastsOnlyUntilEndOfTurn() {
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.HAND, playerA, dontBlink);
        addCard(Zone.HAND, playerA, cloudshift);
        addCard(Zone.BATTLEFIELD, playerA, bears);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, dontBlink);
        castSpell(3, PhaseStep.PRECOMBAT_MAIN, playerA, cloudshift, bears);
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, bears, 1);
        assertLibraryCount(playerA, bears, 0);
    }

    @Test
    public void testACreatureCastFromHandIsUnaffected() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);
        addCard(Zone.HAND, playerA, dontBlink);
        addCard(Zone.HAND, playerA, bears);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, dontBlink);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, bears);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, bears, 1);
    }

    @Test
    public void testACreatureCastFromExileByCascadeIsShuffledToo() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);
        addCard(Zone.HAND, playerA, dontBlink);
        addCard(Zone.HAND, playerA, "Bloodbraid Elf"); // Cascade
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, bears);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, dontBlink);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Bloodbraid Elf");
        setChoice(playerA, true); // cast the cascaded Grizzly Bears
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Bloodbraid Elf", 1); // cast from hand: unaffected
        assertPermanentCount(playerA, bears, 0);
        assertExileCount(playerA, bears, 0);
        assertLibraryCount(playerA, bears, 1);
    }

    @Test
    public void testTheCascadedCreatureEntersWithoutIt() {
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);
        addCard(Zone.HAND, playerA, "Bloodbraid Elf");
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, bears);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Bloodbraid Elf");
        setChoice(playerA, true);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, bears, 1);
        assertLibraryCount(playerA, bears, 0);
    }

    @Test
    public void testCycling() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.HAND, playerA, dontBlink);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Cycling {2}");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, dontBlink, 1);
        assertHandCount(playerA, 1);
    }
}
