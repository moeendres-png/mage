package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class HERBIELovableRobotTest extends CardTestPlayerBase {

    @Test
    public void testManaAbilities() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "H.E.R.B.I.E., Lovable Robot");
        addCard(Zone.BATTLEFIELD, playerA, "Wastes");
        addCard(Zone.HAND, playerA, "Llanowar Elves");

        // {1}, {T}: any color pays for the green spell
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Llanowar Elves");
        setChoice(playerA, "Green"); // color for the {1}, {T} ability

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Llanowar Elves", 1);
    }

    @Test
    public void testSurveilAfterNoncreatureSpell() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, "H.E.R.B.I.E., Lovable Robot");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.LIBRARY, playerA, "Hill Giant");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", playerB);
        addTarget(playerA, "Hill Giant"); // surveil: put into graveyard

        setStopAt(1, PhaseStep.DECLARE_ATTACKERS);
        execute();

        assertGraveyardCount(playerA, "Hill Giant", 1);
    }

    @Test
    public void testNoSurveilAfterOnlyCreatureSpell() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, "H.E.R.B.I.E., Lovable Robot");
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.HAND, playerA, "Llanowar Elves");
        addCard(Zone.LIBRARY, playerA, "Hill Giant");

        // a creature spell does not satisfy "if you've cast a noncreature spell this turn":
        // strict mode would fail on an unexpected surveil choice
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Llanowar Elves");

        setStopAt(1, PhaseStep.DECLARE_ATTACKERS);
        execute();

        assertGraveyardCount(playerA, "Hill Giant", 0);
        assertLibraryCount(playerA, "Hill Giant", 1);
    }
}
