package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class CosmicCrucibleTest extends CardTestPlayerBase {

    @Test
    public void testManaAndCopyOncePerTurn() {
        addCard(Zone.BATTLEFIELD, playerA, "Cosmic Crucible");
        addCard(Zone.HAND, playerA, "Prophetic Prism", 2);

        // four trigger mana pay for both Prisms; only the first one is copied
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Prophetic Prism");
        setChoice(playerA, true); // copy it
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Prophetic Prism");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Prophetic Prism", 3);
        assertHandCount(playerA, 3);
    }
}
