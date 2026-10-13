package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class TheSpearOfBashengaTest extends CardTestPlayerBase {

    private static final String SPEAR = "The Spear of Bashenga";

    @Test
    public void testEntersMakesYouMonarchWhenThereIsNone() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, SPEAR);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 5);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, SPEAR);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        Assert.assertEquals(playerA.getId(), currentGame.getMonarchId());
    }

    @Test
    public void testEntersDoesNotTakeAnExistingCrown() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, SPEAR);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 5);
        runCode("PlayerB is the monarch", 1, PhaseStep.UPKEEP, playerA,
                (info, player, game) -> game.setMonarchId(null, playerB.getId()));

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, SPEAR);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        Assert.assertEquals(playerB.getId(), currentGame.getMonarchId());
    }

    @Test
    public void testAttackingTheMonarchDestroysTappedPermanent() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, SPEAR);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerB, "Sol Ring", 1, true); // tapped nonland permanent
        runCode("PlayerB is the monarch", 1, PhaseStep.UPKEEP, playerA,
                (info, player, game) -> game.setMonarchId(null, playerB.getId()));

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Equip", "Grizzly Bears");
        attack(1, playerA, "Grizzly Bears", playerB);
        addTarget(playerA, "Sol Ring");

        setStopAt(1, PhaseStep.END_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Sol Ring", 1);
        assertLife(playerB, 20 - 4); // +2/+2
        assertTapped("Grizzly Bears", false); // vigilance
    }
}
