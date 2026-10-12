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
}
