package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class HawkeyeAvengingArcherTest extends CardTestPlayerBase {

    @Test
    public void testDrawWhenDamagedCreatureDies() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Hawkeye, Avenging Archer");
        addCard(Zone.BATTLEFIELD, playerB, "Memnite");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{T}: ", "Memnite");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Memnite", 1);
        assertHandCount(playerA, 1);
    }

    @Test
    public void testNoDrawWithoutHawkeyeDamage() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Hawkeye, Avenging Archer");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerB, "Memnite");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", "Memnite");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Memnite", 1);
        assertHandCount(playerA, 0);
    }
}
