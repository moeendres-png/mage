package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class CouncilOfReedsTest extends CardTestPlayerBase {

    private static final String REEDS = "Council of Reeds";

    @Test
    public void testTokenCopyAfterNoncreatureSpellAndLegendRuleOff() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, REEDS);
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.HAND, playerA, "Giant Growth");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Giant Growth", REEDS);

        setStopAt(1, PhaseStep.DECLARE_ATTACKERS);
        execute();

        // the legendary token copy stays next to the original
        assertPermanentCount(playerA, REEDS, 2);
    }

    @Test
    public void testNoTokenWithoutNoncreatureSpell() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, REEDS);

        setStopAt(1, PhaseStep.DECLARE_ATTACKERS);
        execute();

        assertPermanentCount(playerA, REEDS, 1);
    }
}
