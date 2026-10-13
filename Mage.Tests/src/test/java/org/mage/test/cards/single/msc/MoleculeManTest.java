package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class MoleculeManTest extends CardTestPlayerBase {

    @Test
    public void testMiracleZero() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, "Molecule Man");
        addCard(Zone.LIBRARY, playerA, "Island", 3);
        addCard(Zone.LIBRARY, playerA, "Divination");

        setChoice(playerA, true); // reveal (miracle trigger)
        setChoice(playerA, true); // cast for {0}

        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerA, "Divination", 1);
        assertHandCount(playerA, 2);
    }
}
