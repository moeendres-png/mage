package org.mage.test.cards.single.frc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Jhoira, Weatherlight Corsair {4}{B}{B} 4/5
 * Whenever Jhoira enters or attacks, target opponent reveals cards from the top of their library until they reveal a
 * historic permanent card. You put that card onto the battlefield under your control and lose life equal to that
 * permanent's mana value. That player puts the rest of the revealed cards on the bottom of their library in a random order.
 */
public class JhoiraWeatherlightCorsairTest extends CardTestPlayerBase {

    private static final String jhoira = "Jhoira, Weatherlight Corsair";

    @Test
    public void testEntersStealsFirstHistoricPermanent() {
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        addCard(Zone.HAND, playerA, jhoira);
        removeAllCardsFromLibrary(playerB);
        addCard(Zone.LIBRARY, playerB, "Island"); // bottom
        addCard(Zone.LIBRARY, playerB, "Sol Ring"); // historic artifact, mana value 1
        addCard(Zone.LIBRARY, playerB, "Grizzly Bears"); // top, revealed first and not historic

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, jhoira);
        addTarget(playerA, playerB);
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Sol Ring", 1);
        assertLife(playerA, 20 - 1);
        assertLibraryCount(playerB, 2);
        assertLibraryCount(playerB, "Grizzly Bears", 1); // moved to the bottom with the Island
    }

    @Test
    public void testNoHistoricPermanentMovesEverythingToTheBottom() {
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        addCard(Zone.HAND, playerA, jhoira);
        removeAllCardsFromLibrary(playerB);
        addCard(Zone.LIBRARY, playerB, "Island", 2);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, jhoira);
        addTarget(playerA, playerB);
        skipInitShuffling();
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertLife(playerA, 20);
        assertLibraryCount(playerB, 2);
    }
}
