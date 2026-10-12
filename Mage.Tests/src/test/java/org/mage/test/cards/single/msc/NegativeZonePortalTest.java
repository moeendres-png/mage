package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class NegativeZonePortalTest extends CardTestPlayerBase {

    @Test
    public void testExileDrawAndLostFlip() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Negative Zone Portal");
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 2);
        addCard(Zone.GRAVEYARD, playerB, "Grizzly Bears");
        addCard(Zone.GRAVEYARD, playerB, "Hill Giant");
        addCard(Zone.GRAVEYARD, playerB, "Memnite");
        addCard(Zone.GRAVEYARD, playerB, "Silvercoat Lion");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}: ", "Grizzly Bears");
        activateAbility(3, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}: ", "Hill Giant");
        activateAbility(5, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}: ", "Memnite");
        activateAbility(7, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}: ", "Silvercoat Lion");
        setFlipCoinResult(playerA, false);

        setStopAt(9, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerA, "Negative Zone Portal", 1);
        assertExileCount(playerB, 3);
        assertGraveyardCount(playerB, 0);
    }

    @Test
    public void testThreeCreaturesNoFlipAndNoncreatureNoDraw() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, "Negative Zone Portal");
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 2);
        addCard(Zone.GRAVEYARD, playerB, "Grizzly Bears");
        addCard(Zone.GRAVEYARD, playerB, "Hill Giant");
        addCard(Zone.GRAVEYARD, playerB, "Memnite");
        addCard(Zone.GRAVEYARD, playerB, "Lightning Bolt");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}: ", "Lightning Bolt");
        checkHandCount("noncreature: no draw", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, 0);
        activateAbility(3, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}: ", "Grizzly Bears");
        activateAbility(5, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}: ", "Hill Giant");
        activateAbility(7, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}: ", "Memnite");

        // three creature cards exiled: the upkeep trigger's condition is false, no flip is asked
        setStopAt(9, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertPermanentCount(playerA, "Negative Zone Portal", 1);
        assertExileCount(playerB, 4);
        // turns 3, 5, 7, 9 draw steps (4) + three creature exiles (3); turn 1 has no draw
        assertHandCount(playerA, 7);
    }
}
