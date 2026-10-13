package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * N'Yami-Class Mother Ship {6}
 * Artifact — Vehicle
 * Flying, vigilance, haste
 * Whenever this Vehicle deals combat damage to a player, look at the top card of your library. If it's a
 * permanent card, you may put it onto the battlefield. If you don't put it onto the battlefield, put it into
 * your hand.
 * Crew 3
 *
 * @author commander-lab
 */
public class NYamiClassMotherShipTest extends CardTestPlayerBase {

    private static final String SHIP = "N'Yami-Class Mother Ship";

    private void crewAndAttack() {
        addCard(Zone.BATTLEFIELD, playerA, SHIP);
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant"); // power 3 crews it
        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Crew 3");
        setChoice(playerA, "Hill Giant");
        attack(1, playerA, SHIP, playerB);
    }

    @Test
    public void testPermanentOnTopGoesOntoTheBattlefield() {
        setStrictChooseMode(true);
        crewAndAttack();
        skipInitShuffling();
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears"); // permanent card on top
        setChoice(playerA, true); // put it onto the battlefield

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20 - 5);
        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertHandCount(playerA, "Grizzly Bears", 0);
    }

    @Test
    public void testDecliningThePermanentLeavesItInHand() {
        setStrictChooseMode(true);
        crewAndAttack();
        skipInitShuffling();
        addCard(Zone.LIBRARY, playerA, "Grizzly Bears"); // permanent card on top
        setChoice(playerA, false); // don't put it onto the battlefield

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20 - 5);
        assertPermanentCount(playerA, "Grizzly Bears", 0);
        assertHandCount(playerA, "Grizzly Bears", 1);
    }

    @Test
    public void testNonPermanentOnTopGoesStraightToHand() {
        setStrictChooseMode(true);
        crewAndAttack();
        skipInitShuffling();
        addCard(Zone.LIBRARY, playerA, "Lightning Bolt"); // instant, no question asked

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20 - 5);
        assertPermanentCount(playerA, "Lightning Bolt", 0);
        assertHandCount(playerA, "Lightning Bolt", 1);
    }

    @Test
    public void testNoDamageNoLook() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, SHIP);
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant");
        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Crew 3");
        setChoice(playerA, "Hill Giant");
        // no attack: no combat damage, no trigger

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20);
        assertHandCount(playerA, 0);
    }
}
