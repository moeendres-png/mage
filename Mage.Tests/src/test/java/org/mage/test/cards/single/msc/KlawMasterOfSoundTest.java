package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.abilities.keyword.IndestructibleAbility;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class KlawMasterOfSoundTest extends CardTestPlayerBase {

    @Test
    public void testExileAndPlayWithAnyMana() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, "Klaw, Master of Sound");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);
        addCard(Zone.LIBRARY, playerB, "Grizzly Bears");

        attack(1, playerA, "Klaw, Master of Sound", playerB);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Grizzly Bears");

        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 17);
        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertAbility(playerA, "Klaw, Master of Sound", IndestructibleAbility.getInstance(), true);
    }
}
