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

        // Three artifact creature cards satisfy Lorehold Archivist's
        // intervening-if prepare condition at upkeep.
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

        // Prepare rules require a copy of the prepare spell to exist in exile.
        assertExileCount(playerA, PREPARE_SPELL, 1);
    }
}