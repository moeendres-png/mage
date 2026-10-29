package org.mage.test.cards.single.m3c;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Desert Warfare {3}{G}
 * Enchantment
 * Whenever you sacrifice a Desert and whenever a Desert card is put into your graveyard from your hand or library,
 * put that card onto the battlefield under your control at the beginning of your next end step.
 * At the beginning of combat on your turn, if you control five or more Deserts, create that many 1/1 red, green,
 * and white Sand Warrior creature tokens. They gain haste.
 */
public class DesertWarfareTest extends CardTestPlayerBase {

    private static final String warfare = "Desert Warfare";
    private static final String desert = "Desert";
    private static final String sandWarrior = "Sand Warrior Token";

    @Test
    public void testSacrificedDesertReturnsAtTheNextEndStep() {
        addCard(Zone.BATTLEFIELD, playerA, warfare);
        addCard(Zone.BATTLEFIELD, playerA, desert);
        addCard(Zone.BATTLEFIELD, playerA, "Zuran Orb"); // Sacrifice a land: You gain 2 life.

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Sacrifice a land");
        setChoice(playerA, desert);
        checkGraveyardCount("waiting in the graveyard", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, desert, 1);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.CLEANUP);
        execute();

        assertLife(playerA, 22);
        assertPermanentCount(playerA, desert, 1);
        assertGraveyardCount(playerA, desert, 0);
    }

    @Test
    public void testDesertDiscardedFromHandReturns() {
        addCard(Zone.BATTLEFIELD, playerA, warfare);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp");
        addCard(Zone.HAND, playerA, desert);
        addCard(Zone.HAND, playerA, "Raven's Crime"); // {B} sorcery: Target player discards a card. Retrace

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Raven's Crime", playerA);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.CLEANUP);
        execute();

        assertPermanentCount(playerA, desert, 1);
        assertGraveyardCount(playerA, desert, 0);
    }

    @Test
    public void testDesertPutIntoTheGraveyardFromTheLibraryReturns() {
        addCard(Zone.BATTLEFIELD, playerA, warfare);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp");
        addCard(Zone.HAND, playerA, "Entomb"); // {B} instant: search your library for a card, put it into your graveyard
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, desert);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Entomb");
        addTarget(playerA, desert);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.CLEANUP);
        execute();

        assertPermanentCount(playerA, desert, 1);
        assertGraveyardCount(playerA, desert, 0);
    }

    @Test
    public void testOtherCardsInTheGraveyardDoNotReturn() {
        addCard(Zone.BATTLEFIELD, playerA, warfare);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp");
        addCard(Zone.HAND, playerA, "Grizzly Bears");
        addCard(Zone.HAND, playerA, "Raven's Crime");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Raven's Crime", playerA);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.CLEANUP);
        execute();

        assertGraveyardCount(playerA, "Grizzly Bears", 1);
        assertPermanentCount(playerA, "Grizzly Bears", 0);
    }

    @Test
    public void testFiveDesertsMakeFiveHastyWarriors() {
        addCard(Zone.BATTLEFIELD, playerA, warfare);
        addCard(Zone.BATTLEFIELD, playerA, desert, 5);

        runCode("tokens have haste", 1, PhaseStep.DECLARE_ATTACKERS, playerA, (info, player, game) ->
                org.junit.Assert.assertEquals(5, game.getBattlefield().getAllActivePermanents().stream()
                        .filter(p -> p.getName().equals(sandWarrior) && p.hasAbility(mage.abilities.keyword.HasteAbility.getInstance(), game))
                        .count()));
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertPermanentCount(playerA, sandWarrior, 5);
    }

    @Test
    public void testFourDesertsMakeNoWarriors() {
        addCard(Zone.BATTLEFIELD, playerA, warfare);
        addCard(Zone.BATTLEFIELD, playerA, desert, 4);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertPermanentCount(playerA, sandWarrior, 0);
    }
}
