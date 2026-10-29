package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Missy {3}{U}{B}{R} 4/5 legendary creature
 * Whenever another nonartifact creature dies, return it to the battlefield under your control face down and
 * tapped. It's a 2/2 Cyberman artifact creature.
 * At the beginning of your end step, each opponent faces a villainous choice -- Each artifact creature you control
 * deals 1 damage to that opponent, or you draw a card and chaos ensues.
 */
public class MissyTest extends CardTestPlayerBase {

    private static final String missy = "Missy";

    @Test
    public void testNonartifactCreatureReturnsFaceDownTappedUnderMissysController() {
        addCard(Zone.BATTLEFIELD, playerA, missy);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", "Grizzly Bears");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertGraveyardCount(playerB, "Grizzly Bears", 0);
        CybermanAssert.assertCybermen(currentGame, playerA, 1);
        Permanent cyberman = CybermanAssert.faceDown(currentGame, playerA).get(0);
        Assert.assertTrue("returned tapped", cyberman.isTapped());
        Assert.assertEquals(playerA.getId(), cyberman.getControllerId());
        Assert.assertEquals(playerB.getId(), cyberman.getOwnerId());
    }

    @Test
    public void testOwnCreatureAlsoReturns() {
        addCard(Zone.BATTLEFIELD, playerA, missy);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerA, "Savannah Lions");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", "Savannah Lions");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        CybermanAssert.assertCybermen(currentGame, playerA, 1);
    }

    @Test
    public void testArtifactCreatureStaysDead() {
        addCard(Zone.BATTLEFIELD, playerA, missy);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");
        addCard(Zone.BATTLEFIELD, playerB, "Ornithopter"); // 0/2 artifact creature

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", "Ornithopter");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Ornithopter", 1);
        CybermanAssert.assertCybermen(currentGame, playerA, 0);
    }

    @Test
    public void testMissyHerselfDoesNotReturn() {
        addCard(Zone.BATTLEFIELD, playerA, missy);
        addCard(Zone.BATTLEFIELD, playerB, "Swamp", 3);
        addCard(Zone.HAND, playerB, "Murder");

        setChoice(playerB, true); // turn 1 end step: take 1 damage
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Murder", missy);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, missy, 1);
        CybermanAssert.assertCybermen(currentGame, playerA, 0);
        CybermanAssert.assertCybermen(currentGame, playerB, 0);
    }

    @Test
    public void testEndStepDamageChoice() {
        addCard(Zone.BATTLEFIELD, playerA, missy);
        addCard(Zone.BATTLEFIELD, playerA, "Ornithopter");
        addCard(Zone.BATTLEFIELD, playerA, "Wall of Omens"); // not an artifact creature

        setChoice(playerB, true); // each artifact creature deals 1 damage to that opponent
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20 - 1); // one artifact creature
    }

    @Test
    public void testEndStepDrawChoice() {
        addCard(Zone.BATTLEFIELD, playerA, missy);
        addCard(Zone.BATTLEFIELD, playerA, "Ornithopter");

        setChoice(playerB, false); // you draw a card and chaos ensues
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20);
        assertHandCount(playerA, 1); // the card drawn at the end step (the starting player skips the first draw)
    }
}
