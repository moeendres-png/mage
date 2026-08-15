package org.mage.test.cards.abilities.keywords;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

public class PrepareTest extends CardTestPlayerBase {

    private static final String ARCHIVIST = "Lorehold Archivist";
    private static final String PREPARE_SPELL = "Restore Relic";

    @Test
    public void test_PreparingCreatesSpellCopyInExile() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);

        addCard(Zone.GRAVEYARD, playerA, "Ornithopter", 3);

        runCode(
                "Lorehold Archivist becomes prepared",
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                (info, player, game) -> {
                    Permanent archivist = game
                            .getBattlefield()
                            .getAllActivePermanents(player.getId())
                            .stream()
                            .filter(permanent -> ARCHIVIST.equals(permanent.getName()))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    Assert.assertTrue(
                            "Lorehold Archivist must be prepared after its upkeep trigger resolves",
                            archivist.isPrepared()
                    );
                }
        );

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertExileCount(playerA, PREPARE_SPELL, 1);
    }

    @Test
    public void test_PreparedSpellCanBeCastFromExile() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);

        // Three qualifying graveyard cards cause Archivist to become prepared.
        // Solemn is the unique Restore Relic target.
        addCard(Zone.GRAVEYARD, playerA, "Solemn Simulacrum");
        addCard(Zone.GRAVEYARD, playerA, "Ornithopter");
        addCard(Zone.GRAVEYARD, playerA, "Memnite");

        // Restore Relic costs {2}{R}{W}.
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 2);

        // The prepared spell copy should be castable from exile
        // during PlayerA's precombat main phase.
        castSpell(
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                PREPARE_SPELL,
                "Solemn Simulacrum"
        );

        // Decline Solemn Simulacrum's optional ETB search.
        setChoice(playerA, false);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // Restore Relic exiles the targeted graveyard card...
        assertGraveyardCount(playerA, "Solemn Simulacrum", 0);
        assertExileCount(playerA, "Solemn Simulacrum", 1);

        // ...and creates a token copy of it.
        assertPermanentCount(playerA, "Solemn Simulacrum", 1);
    }

    @Test
    public void test_CastingPreparedSpellMakesPermanentUnprepared() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);

        addCard(Zone.GRAVEYARD, playerA, "Solemn Simulacrum");
        addCard(Zone.GRAVEYARD, playerA, "Ornithopter");
        addCard(Zone.GRAVEYARD, playerA, "Memnite");

        // Restore Relic costs {2}{R}{W}.
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 2);

        castSpell(
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                PREPARE_SPELL,
                "Solemn Simulacrum"
        );

        // Decline the token Solemn Simulacrum's optional ETB search.
        setChoice(playerA, false);

        runCode(
                "Lorehold Archivist is unprepared after its prepare spell is cast",
                1,
                PhaseStep.BEGIN_COMBAT,
                playerA,
                (info, player, game) -> {
                    Permanent archivist = game
                            .getBattlefield()
                            .getAllActivePermanents(player.getId())
                            .stream()
                            .filter(permanent -> ARCHIVIST.equals(permanent.getName()))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    Assert.assertFalse(
                            "Lorehold Archivist must become unprepared when its prepare spell is cast",
                            archivist.isPrepared()
                    );
                }
        );

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();
    }

    @Test
    public void test_PrepareCopyDisappearsWhenParentLeavesBattlefield() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);

        // Lorehold Archivist prepares during upkeep if there are at least
        // three artifact and/or creature cards in its owner's graveyard.
        addCard(Zone.GRAVEYARD, playerA, "Solemn Simulacrum");
        addCard(Zone.GRAVEYARD, playerA, "Ornithopter");
        addCard(Zone.GRAVEYARD, playerA, "Memnite");

        // Remove the prepared permanent after its upkeep trigger has resolved.
        addCard(Zone.HAND, playerA, "Unsummon");
        addCard(Zone.BATTLEFIELD, playerA, "Island");

        castSpell(
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                "Unsummon",
                ARCHIVIST
        );

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // The parent permanent is gone...
        assertPermanentCount(playerA, ARCHIVIST, 0);
        assertHandCount(playerA, ARCHIVIST, 1);

        // ...so its associated prepare-spell copy must cease to exist.
        assertExileCount(playerA, PREPARE_SPELL, 0);
    }

    @Test
    public void test_PrepareCopyDisappearsWhenPermanentBecomesUnprepared() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);

        addCard(Zone.GRAVEYARD, playerA, "Solemn Simulacrum");
        addCard(Zone.GRAVEYARD, playerA, "Ornithopter");
        addCard(Zone.GRAVEYARD, playerA, "Memnite");

        runCode(
                "make Lorehold Archivist unprepared without casting its prepare spell",
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                (info, player, game) -> {
                    Permanent archivist = game
                            .getBattlefield()
                            .getAllActivePermanents(player.getId())
                            .stream()
                            .filter(permanent -> ARCHIVIST.equals(permanent.getName()))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    Assert.assertTrue(
                            "Lorehold Archivist must be prepared before this cleanup test",
                            archivist.isPrepared()
                    );

                    archivist.setPrepared(false, game);

                    Assert.assertFalse(
                            "Lorehold Archivist must now be unprepared",
                            archivist.isPrepared()
                    );
                }
        );

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // The parent remains on the battlefield.
        assertPermanentCount(playerA, ARCHIVIST, 1);

        // But its prepare-spell copy must cease to exist.
        assertExileCount(playerA, PREPARE_SPELL, 0);
    }

    @Test
    public void test_NewControllerCanCastPreparedSpell() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);

        // Player A prepares Lorehold Archivist during turn 1 upkeep.
        addCard(Zone.GRAVEYARD, playerA, "Solemn Simulacrum");
        addCard(Zone.GRAVEYARD, playerA, "Memnite");
        addCard(Zone.GRAVEYARD, playerA, "Burnished Hart");

        // Player B needs a legal Restore Relic target after gaining control.
        addCard(Zone.GRAVEYARD, playerB, "Ornithopter");

        // Gain control of Archivist during player B's turn.
        addCard(Zone.HAND, playerB, "Act of Treason");

        // Act of Treason {2}{R} plus Restore Relic {2}{R}{W}.
        addCard(Zone.BATTLEFIELD, playerB, "Mountain", 4);
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 3);

        castSpell(
                2,
                PhaseStep.PRECOMBAT_MAIN,
                playerB,
                "Act of Treason",
                ARCHIVIST
        );

        // The prepare-copy must follow the permanent's current controller.
        castSpell(
                2,
                PhaseStep.POSTCOMBAT_MAIN,
                playerB,
                PREPARE_SPELL,
                "Ornithopter"
        );

        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.END_TURN);
        execute();

        // Player B successfully used Restore Relic from exile.
        assertGraveyardCount(playerB, "Ornithopter", 0);
        assertExileCount(playerB, "Ornithopter", 1);
        assertPermanentCount(playerB, "Ornithopter", 1);
    }

    @Test
    public void test_AlreadyPreparedPermanentDoesNotCreateSecondCopy() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);

        // The condition remains true across both of player A's upkeeps.
        addCard(Zone.GRAVEYARD, playerA, "Solemn Simulacrum");
        addCard(Zone.GRAVEYARD, playerA, "Ornithopter");
        addCard(Zone.GRAVEYARD, playerA, "Memnite");

        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        // The first upkeep prepares Archivist. The second upkeep must not
        // create another prepare-spell copy while Archivist is still prepared.
        assertPermanentCount(playerA, ARCHIVIST, 1);
        assertExileCount(playerA, PREPARE_SPELL, 1);
    }

    @Test
    public void test_TargetEffectCreatesPrepareSpellCopy() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);
        addCard(Zone.BATTLEFIELD, playerA, "Skycoach Waypoint");

        // Pay {3} for Skycoach Waypoint's prepare ability.
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);

        activateAbility(
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                "{3}, {T}: Target creature becomes prepared",
                ARCHIVIST
        );

        runCode(
                "Lorehold Archivist is prepared by Skycoach Waypoint",
                1,
                PhaseStep.BEGIN_COMBAT,
                playerA,
                (info, player, game) -> {
                    Permanent archivist = game
                            .getBattlefield()
                            .getAllActivePermanents(player.getId())
                            .stream()
                            .filter(permanent -> ARCHIVIST.equals(permanent.getName()))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    Assert.assertTrue(
                            "Lorehold Archivist must become prepared",
                            archivist.isPrepared()
                    );
                }
        );

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        // Becoming prepared through a target effect must create the same
        // prepare-spell copy as becoming prepared through the card's own effect.
        assertExileCount(playerA, PREPARE_SPELL, 1);
    }

    @Test
    public void test_TargetEffectPrepareCopyCanBeCast() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);
        addCard(Zone.BATTLEFIELD, playerA, "Skycoach Waypoint");

        // Only one artifact/creature card is in the graveyard, so
        // Lorehold Archivist's own upkeep trigger cannot prepare it.
        addCard(Zone.GRAVEYARD, playerA, "Solemn Simulacrum");

        // Turn 1: {3} for Skycoach Waypoint.
        // Turn 3: the lands untap and provide {2}{R}{W} for Restore Relic.
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");

        activateAbility(
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                "{3}, {T}: Target creature becomes prepared",
                ARCHIVIST
        );

        castSpell(
                3,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                PREPARE_SPELL,
                "Solemn Simulacrum"
        );

        // Decline Solemn Simulacrum's ETB search choice in the test harness.
        setChoice(playerA, false);

        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.BEGIN_COMBAT);
        execute();

        // Restore Relic was successfully cast and resolved.
        assertGraveyardCount(playerA, "Solemn Simulacrum", 0);
        assertExileCount(playerA, "Solemn Simulacrum", 1);
        assertPermanentCount(playerA, "Solemn Simulacrum", 1);
    }

    @Test
    public void test_CancelledPrepareSpellCastKeepsPermanentPrepared() {
        addCard(Zone.BATTLEFIELD, playerA, ARCHIVIST);

        // Archivist prepares during turn 1 upkeep.
        addCard(Zone.GRAVEYARD, playerA, "Solemn Simulacrum");
        addCard(Zone.GRAVEYARD, playerA, "Memnite");
        addCard(Zone.GRAVEYARD, playerA, "Burnished Hart");

        // Restore Relic is affordable, but the player will cancel
        // during mana payment instead of completing the cast.
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Plains");

        disableManaAutoPayment(playerA);

        castSpell(
                1,
                PhaseStep.PRECOMBAT_MAIN,
                playerA,
                PREPARE_SPELL,
                "Solemn Simulacrum"
        );

        setChoice(
                playerA,
                org.mage.test.player.TestPlayer.MANA_CANCEL
        );
        setChoice(
                playerA,
                org.mage.test.player.TestPlayer.SKIP_FAILED_COMMAND
        );

        runCode(
                "cancelled prepare-spell cast preserves prepare state",
                1,
                PhaseStep.BEGIN_COMBAT,
                playerA,
                (info, player, game) -> {
                    Permanent archivist = game
                            .getBattlefield()
                            .getAllActivePermanents(player.getId())
                            .stream()
                            .filter(permanent -> ARCHIVIST.equals(permanent.getName()))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    Assert.assertTrue(
                            "Cancelling the prepare-spell cast must not unprepare Lorehold Archivist",
                            archivist.isPrepared()
                    );
                }
        );

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        // The cancelled cast must leave the complete prepare relationship intact.
        assertExileCount(playerA, PREPARE_SPELL, 1);
        assertGraveyardCount(playerA, "Solemn Simulacrum", 1);
        assertPermanentCount(playerA, "Solemn Simulacrum", 0);
    }

    @org.junit.Test
    public void test_TargetPrepareDoesNothingForCreatureWithoutPrepareSpell() {
        // Skycoach Waypoint
        // {3}, {T}: Target creature becomes prepared.
        //
        // A creature without a prepare spell can't become prepared.
        addCard(mage.constants.Zone.BATTLEFIELD, playerA, "Skycoach Waypoint");
        addCard(mage.constants.Zone.BATTLEFIELD, playerA, "Mountain", 3);
        addCard(mage.constants.Zone.BATTLEFIELD, playerA, "Grizzly Bears");

        activateAbility(
                1,
                mage.constants.PhaseStep.PRECOMBAT_MAIN,
                playerA,
                "{3}, {T}: Target creature becomes prepared",
                "Grizzly Bears"
        );
        waitStackResolved(1, mage.constants.PhaseStep.PRECOMBAT_MAIN);

        runCode(
                "non-prepare creature must remain unprepared",
                1,
                mage.constants.PhaseStep.PRECOMBAT_MAIN,
                playerA,
                (info, player, game) -> {
                    mage.game.permanent.Permanent bears = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent -> permanent.getControllerId().equals(player.getId()))
                            .filter(permanent -> permanent.getName().equals("Grizzly Bears"))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Grizzly Bears not found"));

                    org.junit.Assert.assertFalse(
                            "Creature without a prepare spell must remain unprepared",
                            bears.isPrepared()
                    );

                    org.junit.Assert.assertEquals(
                            "Preparing a creature without a prepare spell must not create an exile copy",
                            0,
                            game.getExile().getAllCards(game).size()
                    );
                }
        );

        setStrictChooseMode(true);
        setStopAt(1, mage.constants.PhaseStep.END_TURN);
        execute();
    }

    @org.junit.Test
    public void test_CanPrepareAgainAfterPreparedSpellWasCast() {
        // Lorehold Archivist prepares at upkeep with at least three
        // artifact and/or creature cards in its controller's graveyard.
        // Start with four so that after Restore Relic #1 exiles one,
        // three remain and the Archivist can prepare again next upkeep.
        addCard(mage.constants.Zone.BATTLEFIELD, playerA, "Lorehold Archivist");
        addCard(mage.constants.Zone.BATTLEFIELD, playerA, "Mountain", 2);
        addCard(mage.constants.Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(mage.constants.Zone.GRAVEYARD, playerA, "Grizzly Bears", 4);

        // First prepare cycle.
        waitStackResolved(1, mage.constants.PhaseStep.UPKEEP);
        runCode(
                "first prepare created one castable copy",
                1,
                mage.constants.PhaseStep.UPKEEP,
                playerA,
                (info, player, game) -> {
                    mage.game.permanent.Permanent archivist = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent -> permanent.getControllerId().equals(player.getId()))
                            .filter(permanent -> permanent.getName().equals("Lorehold Archivist"))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    org.junit.Assert.assertTrue(
                            "Lorehold Archivist must be prepared after first upkeep trigger",
                            archivist.isPrepared()
                    );

                    long copies = game.getExile().getAllCards(game)
                            .stream()
                            .filter(card -> card.getName().equals("Restore Relic"))
                            .count();

                    org.junit.Assert.assertEquals(
                            "First prepare must create exactly one Restore Relic copy in exile",
                            1L,
                            copies
                    );
                }
        );

        castSpell(
                1,
                mage.constants.PhaseStep.PRECOMBAT_MAIN,
                playerA,
                "Restore Relic",
                "Grizzly Bears"
        );
        waitStackResolved(1, mage.constants.PhaseStep.PRECOMBAT_MAIN);

        runCode(
                "first cast completed prepare lifecycle",
                1,
                mage.constants.PhaseStep.PRECOMBAT_MAIN,
                playerA,
                (info, player, game) -> {
                    mage.game.permanent.Permanent archivist = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent -> permanent.getControllerId().equals(player.getId()))
                            .filter(permanent -> permanent.getName().equals("Lorehold Archivist"))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    org.junit.Assert.assertFalse(
                            "Casting the first prepared spell must unprepare Lorehold Archivist",
                            archivist.isPrepared()
                    );

                    long copies = game.getExile().getAllCards(game)
                            .stream()
                            .filter(card -> card.getName().equals("Restore Relic"))
                            .count();

                    org.junit.Assert.assertEquals(
                            "First Restore Relic prepare copy must be gone after it is cast",
                            0L,
                            copies
                    );

                    org.junit.Assert.assertEquals(
                            "Exactly three Grizzly Bears must remain in the graveyard after first Restore Relic",
                            3L,
                            player.getGraveyard().getCards(game)
                                    .stream()
                                    .filter(card -> card.getName().equals("Grizzly Bears"))
                                    .count()
                    );
                }
        );

        // Turn 2 belongs to player B. On player A's next upkeep (turn 3),
        // the remaining three creature cards must allow a fresh prepare.
        waitStackResolved(3, mage.constants.PhaseStep.UPKEEP);
        runCode(
                "second prepare created a fresh copy",
                3,
                mage.constants.PhaseStep.UPKEEP,
                playerA,
                (info, player, game) -> {
                    mage.game.permanent.Permanent archivist = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent -> permanent.getControllerId().equals(player.getId()))
                            .filter(permanent -> permanent.getName().equals("Lorehold Archivist"))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    org.junit.Assert.assertTrue(
                            "Lorehold Archivist must become prepared again on the later upkeep",
                            archivist.isPrepared()
                    );

                    long copies = game.getExile().getAllCards(game)
                            .stream()
                            .filter(card -> card.getName().equals("Restore Relic"))
                            .count();

                    org.junit.Assert.assertEquals(
                            "Re-prepare must create exactly one new Restore Relic copy in exile",
                            1L,
                            copies
                    );
                }
        );

        // Prove that the newly created copy is actually castable too.
        castSpell(
                3,
                mage.constants.PhaseStep.PRECOMBAT_MAIN,
                playerA,
                "Restore Relic",
                "Grizzly Bears"
        );
        waitStackResolved(3, mage.constants.PhaseStep.PRECOMBAT_MAIN);

        runCode(
                "second cast completed prepare lifecycle",
                3,
                mage.constants.PhaseStep.PRECOMBAT_MAIN,
                playerA,
                (info, player, game) -> {
                    mage.game.permanent.Permanent archivist = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent -> permanent.getControllerId().equals(player.getId()))
                            .filter(permanent -> permanent.getName().equals("Lorehold Archivist"))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Lorehold Archivist not found"));

                    org.junit.Assert.assertFalse(
                            "Casting the second prepared spell must unprepare Lorehold Archivist again",
                            archivist.isPrepared()
                    );

                    long copies = game.getExile().getAllCards(game)
                            .stream()
                            .filter(card -> card.getName().equals("Restore Relic"))
                            .count();

                    org.junit.Assert.assertEquals(
                            "Second Restore Relic prepare copy must be gone after it is cast",
                            0L,
                            copies
                    );
                }
        );

        setStrictChooseMode(true);
        setStopAt(3, mage.constants.PhaseStep.END_TURN);
        execute();
    }

    @org.junit.Test
    public void test_NaktamunLorespinnerPrepareLifecycle() {
        // Naktamun Lorespinner
        // At the beginning of your upkeep, if a player has one or fewer
        // cards in hand, this creature becomes prepared.
        // Prepare spell: Wheel of Fortune {2}{R}.
        addCard(mage.constants.Zone.BATTLEFIELD, playerA, "Naktamun Lorespinner");
        addCard(mage.constants.Zone.BATTLEFIELD, playerA, "Mountain", 3);

        // Make the intervening-if condition explicit: player B has exactly
        // one card in hand at player A's first upkeep.
        addCard(mage.constants.Zone.HAND, playerA, "Plains", 2);
        addCard(mage.constants.Zone.HAND, playerB, "Island", 1);

        // Wheel of Fortune must be able to draw seven for both players
        // without introducing an empty-library loss into this test.
        addCard(mage.constants.Zone.LIBRARY, playerA, "Plains", 7);
        addCard(mage.constants.Zone.LIBRARY, playerB, "Island", 7);

        waitStackResolved(1, mage.constants.PhaseStep.UPKEEP);

        runCode(
                "Naktamun prepares and creates Wheel of Fortune copy",
                1,
                mage.constants.PhaseStep.UPKEEP,
                playerA,
                (info, player, game) -> {
                    mage.game.permanent.Permanent naktamun = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent -> permanent.getControllerId().equals(player.getId()))
                            .filter(permanent -> permanent.getName().equals("Naktamun Lorespinner"))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Naktamun Lorespinner not found"));

                    org.junit.Assert.assertTrue(
                            "Naktamun must become prepared when a player has one or fewer cards in hand",
                            naktamun.isPrepared()
                    );

                    long copies = game.getExile().getAllCards(game)
                            .stream()
                            .filter(card -> card.getName().equals("Wheel of Fortune"))
                            .count();

                    org.junit.Assert.assertEquals(
                            "Preparing Naktamun must create exactly one Wheel of Fortune copy in exile",
                            1L,
                            copies
                    );
                }
        );

        // This must find and cast the prepared spell copy from exile.
        castSpell(
                1,
                mage.constants.PhaseStep.PRECOMBAT_MAIN,
                playerA,
                "Wheel of Fortune"
        );
        waitStackResolved(1, mage.constants.PhaseStep.PRECOMBAT_MAIN);

        runCode(
                "Naktamun prepared spell resolves correctly",
                1,
                mage.constants.PhaseStep.PRECOMBAT_MAIN,
                playerA,
                (info, player, game) -> {
                    mage.game.permanent.Permanent naktamun = game.getBattlefield()
                            .getAllActivePermanents()
                            .stream()
                            .filter(permanent -> permanent.getControllerId().equals(player.getId()))
                            .filter(permanent -> permanent.getName().equals("Naktamun Lorespinner"))
                            .findFirst()
                            .orElseThrow(() -> new AssertionError("Naktamun Lorespinner not found"));

                    org.junit.Assert.assertFalse(
                            "Casting Wheel of Fortune prepare copy must unprepare Naktamun",
                            naktamun.isPrepared()
                    );

                    long copies = game.getExile().getAllCards(game)
                            .stream()
                            .filter(card -> card.getName().equals("Wheel of Fortune"))
                            .count();

                    org.junit.Assert.assertEquals(
                            "Wheel of Fortune prepare copy must be gone from exile after casting",
                            0L,
                            copies
                    );

                    org.junit.Assert.assertEquals(
                            "Player A must draw seven from Wheel of Fortune",
                            7,
                            player.getHand().size()
                    );

                    mage.players.Player opponent = game.getPlayer(playerB.getId());
                    if (opponent == null) {
                        throw new AssertionError("Player B not found");
                    }

                    org.junit.Assert.assertEquals(
                            "Player B must draw seven from Wheel of Fortune",
                            7,
                            opponent.getHand().size()
                    );
                }
        );

        setStrictChooseMode(true);
        setStopAt(1, mage.constants.PhaseStep.END_TURN);
        execute();
    }
}
