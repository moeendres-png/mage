package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class DragonManReformedRobotTest extends CardTestPlayerBase {

    @Test
    public void testPower() {
        addCard(Zone.BATTLEFIELD, playerA, "Dragon Man, Reformed Robot");
        addCard(Zone.BATTLEFIELD, playerA, "Mind Stone");
        addCard(Zone.GRAVEYARD, playerA, "Divination");
        addCard(Zone.GRAVEYARD, playerA, "Hill Giant");

        setStopAt(1, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertPowerToughness(playerA, "Dragon Man, Reformed Robot", 3, 5);
    }

    @Test
    public void testCastFromGraveyardByDiscarding() {
        addCard(Zone.GRAVEYARD, playerA, "Dragon Man, Reformed Robot");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerA, "Tundra", 4);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Dragon Man, Reformed Robot");
        setChoice(playerA, "Lightning Bolt");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Dragon Man, Reformed Robot", 1);
        assertGraveyardCount(playerA, "Lightning Bolt", 1);
        assertPowerToughness(playerA, "Dragon Man, Reformed Robot", 1, 5);
    }
}
