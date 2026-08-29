package forge.gamesimulationtests;

import forge.ai.AITest;
import forge.game.Game;
import forge.game.card.Card;
import forge.game.phase.PhaseType;
import forge.game.player.Player;
import forge.game.zone.ZoneType;
import org.testng.Assert;
import org.testng.annotations.Test;

/**
 * WS16 executable, actual-card witness.  This source is copied into the
 * pinned Forge checkout only for the qualification run; it never changes the
 * Forge implementation.  Jwar Isle Refuge's real pinned script has both the
 * Moved replacement (enters tapped) and a ChangesZone ETB trigger (gain 1).
 */
public class Ws16JwarIsleRefugeWitnessTest extends AITest {

    @Test
    public void replacementPrecedesEtbTriggerAndTriggerUsesStack() {
        final Game game = initAndCreateGame();
        final Player player = game.getPlayers().get(0);
        game.getPhaseHandler().devModeSet(PhaseType.MAIN1, player);

        final Card refuge = addCardToZone("Jwar Isle Refuge", player, ZoneType.Hand);
        final int lifeBefore = player.getLife();
        System.out.println("WS16_TRACE event=initial card=Jwar_Isle_Refuge zone=Hand life=" + lifeBefore);

        game.getAction().moveTo(ZoneType.Battlefield, refuge, null, null);

        // The replacement effect modifies entry; it is not a post-entry state
        // based action.  The zone and tap assertions exercise the actual Moved
        // replacement in the pinned card script.
        Assert.assertTrue(refuge.isInZone(ZoneType.Battlefield), "refuge must enter the battlefield");
        Assert.assertTrue(refuge.isTapped(), "Moved replacement must make refuge enter tapped");
        Assert.assertEquals(player.getLife(), lifeBefore,
                "ETB trigger must be pending, rather than resolve during zone movement");
        Assert.assertFalse(game.getStack().isEmpty(), "ETB trigger must be placed on the stack");
        System.out.println("WS16_TRACE event=after_move zone=Battlefield tapped=true life=" + player.getLife()
                + " stack_nonempty=true");

        playUntilStackClear(game);

        Assert.assertEquals(player.getLife(), lifeBefore + 1,
                "ChangesZone trigger must resolve after it is placed on the stack");
        Assert.assertTrue(game.getStack().isEmpty(), "trigger resolution must empty the stack");
        System.out.println("WS16_TRACE event=final zone=Battlefield tapped=true life=" + player.getLife()
                + " stack_empty=true");
    }
}
