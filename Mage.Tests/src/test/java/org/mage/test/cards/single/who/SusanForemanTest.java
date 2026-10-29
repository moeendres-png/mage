package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.SubType;
import mage.constants.Zone;
import mage.game.command.Plane;
import mage.game.command.CommandObject;
import mage.abilities.keyword.DoctorsCompanionAbility;
import mage.utils.SystemUtil;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Susan Foreman {1}{G}
 * Legendary Creature -- Time Lord 1/1
 * If you would planeswalk, instead look at the top two cards of your planar deck, put one on the bottom of your
 * planar deck and the other on top, then planeswalk.
 * {T}: Add {G}.
 * Doctor's companion
 */
public class SusanForemanTest extends CardTestPlayerBase {

    private static final String susan = "Susan Foreman";

    @Test
    public void testItIsALegendaryTimeLordWithDoctorsCompanionThatTapsForGreen() {
        addCard(Zone.BATTLEFIELD, playerA, susan);
        addCard(Zone.BATTLEFIELD, playerA, "Forest");
        addCard(Zone.HAND, playerA, "Grizzly Bears"); // {1}{G}: Susan's {G} plus the Forest

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Grizzly Bears");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertTapped(susan, true);
        assertType(susan, mage.constants.CardType.CREATURE, true);
        assertSubtype(susan, SubType.TIME_LORD);
        Assert.assertTrue(currentGame.getBattlefield().getAllActivePermanents().stream()
                .anyMatch(p -> p.getName().equals(susan) && p.isLegendary(currentGame)));
        assertPowerToughness(playerA, susan, 1, 1);
        assertAbility(playerA, susan, DoctorsCompanionAbility.getInstance(), true);
    }

    @Test
    public void testPlaneswalkingWithItStillPutsThePlaneIntoPlay() {
        addCard(Zone.BATTLEFIELD, playerA, susan);

        // There is no planar deck in this engine; the replacement applies, has nothing to reorder and the plane arrives.
        runCode("planeswalk", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Assert.assertTrue(SystemUtil.putPlaneToGame(game, player, "BantPlane"));
        });
        runCode("check", 1, PhaseStep.BEGIN_COMBAT, playerA, (info, player, game) -> {
            boolean planePresent = false;
            for (CommandObject object : game.getState().getCommand()) {
                planePresent |= object instanceof Plane;
            }
            Assert.assertTrue("the plane is in the command zone", planePresent);
        });
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }
}
