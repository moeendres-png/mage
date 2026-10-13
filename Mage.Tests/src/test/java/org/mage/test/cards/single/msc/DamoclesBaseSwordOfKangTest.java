package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class DamoclesBaseSwordOfKangTest extends CardTestPlayerBase {

    private static final String BASE = "Damocles Base, Sword of Kang";

    private void crewAndAttack() {
        addCard(Zone.BATTLEFIELD, playerA, BASE);
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant"); // power 3 crews it
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");
        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Crew 3");
        setChoice(playerA, "Hill Giant");
        attack(1, playerA, BASE, playerB);
    }

    @Test
    public void testDefenderSacrifices() {
        setStrictChooseMode(true);
        crewAndAttack();
        setChoice(playerB, true); // first villainous option: sacrifice a nontoken creature
        setChoice(playerB, "Grizzly Bears");

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20 - 5);
        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertHandCount(playerA, 0);
    }

    @Test
    public void testDefenderLosesLifeAndYouDraw() {
        setStrictChooseMode(true);
        crewAndAttack();
        setChoice(playerB, false); // second option: lose 2 life, attacker draws two

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 20 - 5 - 2);
        assertPermanentCount(playerB, "Grizzly Bears", 1);
        assertHandCount(playerA, 2);
    }
}
