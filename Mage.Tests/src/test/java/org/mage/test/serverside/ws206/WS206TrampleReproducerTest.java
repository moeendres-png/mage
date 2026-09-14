package org.mage.test.serverside.ws206;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * WS206 PRE_FIX reproducer (actual cards, native engine).
 *
 * Shape: 6/6 trample (Colossal Dreadmaw) blocked by 2x 2/2
 * (Grizzly Bears + Silvercoat Lion). Lethal sum = 4, power = 6.
 *
 * Illegal attempt: 4 to Bears, 0 to Lion, 2 through.
 * Aggregate to blockers (4) meets the pre-fix totalMin (= lethal sum 4),
 * but Lion receives 0 < lethal 2 while positive damage tramples through.
 * Per CR 702.19b this complete assignment is illegal and must be rejected
 * before damage is dealt.
 *
 * PRE_FIX result (engine without WS206 validation): BUG_CONFIRMED — the
 * illegal distribution executed as-is (Bears 4/dies, Lion 0/survives,
 * defender takes 2). Recorded in WS206 PRE_FIX evidence; this test now
 * asserts POST_FIX behavior.
 *
 * POST_FIX expectation: the engine rejects the illegal 4/0 attempt,
 * re-requests, and the corrected 2/2 attempt executes (both blockers take
 * lethal 2 and die, 2 tramples to the defender).
 */
public class WS206TrampleReproducerTest extends CardTestPlayerBase {

    @Test
    public void testIllegalTrampleThroughWithBlockerBelowLethal() {
        addCard(Zone.BATTLEFIELD, playerA, "Colossal Dreadmaw"); // 6/6 trample
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "Colossal Dreadmaw");
        block(1, playerB, "Grizzly Bears", "Colossal Dreadmaw");
        block(1, playerB, "Silvercoat Lion", "Colossal Dreadmaw");

        // First attempt is illegal (4/0 + 2 through) and must be rejected;
        // second attempt is legal (2/2 + 2 through) and must execute.
        setChoiceAmount(playerA, 4, 0, 2, 2);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        // POST_FIX signature: illegal rejected, legal retry executed
        assertLife(playerB, 18); // 6 - 2 - 2 = 2 through
        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertPermanentCount(playerB, "Silvercoat Lion", 0);
        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertGraveyardCount(playerB, "Silvercoat Lion", 1);
    }
}
