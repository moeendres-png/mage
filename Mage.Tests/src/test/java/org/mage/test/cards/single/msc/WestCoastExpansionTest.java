package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class WestCoastExpansionTest extends CardTestPlayerBase {

    private static final String WCE = "West Coast Expansion";
    private static final String HERO = "Hercules, Olympian Hero"; // {3}{W}{W} Hero creature

    @Test
    public void testXFiveDrawsAndCastsHeroFree() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, WCE);
        addCard(Zone.HAND, playerA, HERO);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 7);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, WCE);
        setChoiceAmount(playerA, 5); // X = 5
        setChoice(playerA, true); // cast the only Hero in hand for free (auto-selected)

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, HERO, 1);
        assertHandCount(playerA, 5);
    }

    @Test
    public void testXFourNoFreeCast() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, WCE);
        addCard(Zone.HAND, playerA, HERO);
        addCard(Zone.BATTLEFIELD, playerA, "Island", 6);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, WCE);
        setChoiceAmount(playerA, 4); // X = 4: no free cast is offered

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, HERO, 0);
        assertHandCount(playerA, 4 + 1);
    }
}
