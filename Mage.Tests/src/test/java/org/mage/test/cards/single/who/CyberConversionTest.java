package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Cyber Conversion {U}{U} instant
 * Turn target creature face down. It's a 2/2 Cyberman artifact creature.
 */
public class CyberConversionTest extends CardTestPlayerBase {

    private static final String conversion = "Cyber Conversion";

    @Test
    public void testTargetBecomesFaceDownCyberman() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.HAND, playerA, conversion);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, conversion, "Grizzly Bears");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, conversion, 1);
        assertPermanentCount(playerB, "Grizzly Bears", 0); // face down: no name
        CybermanAssert.assertCybermen(currentGame, playerB, 1);
    }

    @Test
    public void testBigCreatureShrinksToTwoByTwo() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 2);
        addCard(Zone.HAND, playerA, conversion);
        addCard(Zone.BATTLEFIELD, playerB, "Craw Wurm"); // 6/4

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, conversion, "Craw Wurm");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        CybermanAssert.assertCybermen(currentGame, playerB, 1);
        org.junit.Assert.assertEquals(2, CybermanAssert.faceDown(currentGame, playerB).get(0).getPower().getValue());
        org.junit.Assert.assertEquals(2, CybermanAssert.faceDown(currentGame, playerB).get(0).getToughness().getValue());
    }
}
