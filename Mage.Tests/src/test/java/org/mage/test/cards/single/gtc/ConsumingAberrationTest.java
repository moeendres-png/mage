package org.mage.test.cards.single.gtc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class ConsumingAberrationTest extends CardTestPlayerBase {

    private static final String ABERRATION = "Consuming Aberration"; // {3}{U}{B}

    @Test
    public void testSizeCountsOpponentGraveyard() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, ABERRATION);
        addCard(Zone.BATTLEFIELD, playerA, "Underground Sea", 5);
        addCard(Zone.GRAVEYARD, playerB, "Grizzly Bears", 3);
        addCard(Zone.GRAVEYARD, playerA, "Grizzly Bears", 2); // own graveyard does not count

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, ABERRATION);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPowerToughness(playerA, ABERRATION, 3, 3);
    }

    @Test
    public void testCastTriggerMillsUntilLand() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, ABERRATION);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 3);
        addCard(Zone.HAND, playerA, "Divination");
        addCard(Zone.GRAVEYARD, playerB, "Grizzly Bears"); // keeps the 0/0 alive until the trigger
        addCard(Zone.LIBRARY, playerB, "Grizzly Bears", 2);
        addCard(Zone.LIBRARY, playerB, "Forest");
        addCard(Zone.LIBRARY, playerB, "Grizzly Bears", 2);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Divination");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        int milled = currentGame.getPlayer(playerB.getId()).getGraveyard().size();
        // at least the revealed land joins the card already there, and the size follows it
        Assert.assertTrue("revealed cards must be put into the graveyard", milled >= 2);
        assertPowerToughness(playerA, ABERRATION, milled, milled);
        assertGraveyardCount(playerA, "Divination", 1);
    }
}
