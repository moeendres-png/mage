package org.mage.test.cards.single.tmc;

import mage.abilities.keyword.FlyingAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class FootChopperTest extends CardTestPlayerBase {

    private static final String CHOPPER = "Foot Chopper";

    @Test
    public void testNinjaTokenEquippedAndFlying() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, CHOPPER);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, CHOPPER);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Ninja Token", 1);
        assertAttachedTo(playerA, CHOPPER, "Ninja Token", true);
        assertAbility(playerA, "Ninja Token", FlyingAbility.getInstance(), true);
    }

    @Test
    public void testSacrificeAfterDamageDrawsPower() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant");
        addCard(Zone.BATTLEFIELD, playerA, CHOPPER);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Equip", "Hill Giant");
        attack(1, playerA, "Hill Giant", playerB);
        setChoice(playerA, true); // sacrifice it

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertLife(playerB, 17);
        assertGraveyardCount(playerA, "Hill Giant", 1);
        assertHandCount(playerA, 3);
    }

    @Test
    public void testDeclineSacrifice() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Hill Giant");
        addCard(Zone.BATTLEFIELD, playerA, CHOPPER);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Equip", "Hill Giant");
        attack(1, playerA, "Hill Giant", playerB);
        setChoice(playerA, false);

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertPermanentCount(playerA, "Hill Giant", 1);
        assertHandCount(playerA, 0);
    }
}
