package org.mage.test.cards.single.sos;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * {@link mage.cards.c.CoerciveImpetus Coercive Impetus}: Enchanted creature gets +1/+1 and is goaded.
 * (The card used to give +2/+2.)
 *
 * @author commander-lab
 */
public class CoerciveImpetusTest extends CardTestPlayerBase {

    @Test
    public void testEnchantedCreatureGetsPlusOnePlusOne() {
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 3);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.HAND, playerA, "Coercive Impetus");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Coercive Impetus", "Grizzly Bears");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertAttachedTo(playerA, "Coercive Impetus", "Grizzly Bears", true);
        assertPowerToughness(playerA, "Grizzly Bears", 3, 3);
    }
}
