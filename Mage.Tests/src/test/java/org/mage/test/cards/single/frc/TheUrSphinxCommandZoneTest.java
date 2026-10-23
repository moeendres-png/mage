package org.mage.test.cards.single.frc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommanderDuelBase;

/**
 * The Ur-Sphinx: eminence -- as long as it is in the command zone or on the battlefield, other Sphinx spells you cast
 * cost {1} less to cast.
 */
public class TheUrSphinxCommandZoneTest extends CardTestCommanderDuelBase {

    @Test
    public void testReducesOtherSphinxSpellsFromCommandZone() {
        addCard(Zone.COMMAND, playerA, "The Ur-Sphinx");
        addCard(Zone.BATTLEFIELD, playerA, "Island", 6);
        addCard(Zone.HAND, playerA, "Sphinx Ambassador"); // {5}{U}{U}

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Sphinx Ambassador");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Sphinx Ambassador", 1);
    }
}
