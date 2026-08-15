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
}
