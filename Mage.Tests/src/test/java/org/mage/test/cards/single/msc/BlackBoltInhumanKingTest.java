package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class BlackBoltInhumanKingTest extends CardTestPlayerBase {

    private static final String BOLT = "Black Bolt, Inhuman King";

    @Test
    public void testNoncreatureSpellPumps() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, BOLT);
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.HAND, playerA, "Giant Growth");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Giant Growth", BOLT);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // 3/3 + 2/2 (Black Bolt trigger) + 3/3 (Giant Growth)
        assertPowerToughness(playerA, BOLT, 8, 8);
    }

    @Test
    public void testLethalVoiceDestroysThatOpponentsPermanent() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, BOLT);
        addCard(Zone.BATTLEFIELD, playerB, "Mountain");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.HAND, playerB, "Shock");

        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Shock", BOLT);
        addTarget(playerA, "Grizzly Bears"); // Lethal Voice

        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertPermanentCount(playerA, BOLT, 1); // 3/3 survives Shock
    }
}
