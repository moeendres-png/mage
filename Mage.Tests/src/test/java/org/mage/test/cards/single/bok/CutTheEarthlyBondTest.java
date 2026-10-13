package org.mage.test.cards.single.bok;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class CutTheEarthlyBondTest extends CardTestPlayerBase {

    @Test
    public void testReturnsEnchantedPermanent() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 3); // a blue source stays open after Pacifism
        addCard(Zone.HAND, playerA, "Pacifism"); // {1}{W}
        addCard(Zone.HAND, playerA, "Cut the Earthly Bond"); // {U}

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Pacifism", "Grizzly Bears");
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Cut the Earthly Bond", "Grizzly Bears");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertHandCount(playerB, "Grizzly Bears", 1);
        assertGraveyardCount(playerA, "Pacifism", 1);
        assertGraveyardCount(playerA, "Cut the Earthly Bond", 1);
    }

    @Test
    public void testUnenchantedPermanentIsNoTarget() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.HAND, playerA, "Cut the Earthly Bond");

        checkPlayableAbility("no enchanted target", 1, PhaseStep.PRECOMBAT_MAIN, playerA,
                "Cast Cut the Earthly Bond", false);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
