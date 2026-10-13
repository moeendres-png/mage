package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.permanent.Permanent;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class GloriousPurposeTest extends CardTestPlayerBase {

    private static final String PURPOSE = "Glorious Purpose";
    // {1}{W} 2/1 "When Raffine's Informant enters the battlefield, it connives."
    private static final String INFORMANT = "Raffine's Informant";

    @Test
    public void testConniveAddsCreatureAndPlanCounter() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, PURPOSE);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.HAND, playerA, INFORMANT);
        addCard(Zone.HAND, playerA, "Plains");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, INFORMANT);
        setChoice(playerA, "Plains"); // connive: discard a land, so connive itself adds no counter

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        // the only +1/+1 counter comes from Glorious Purpose (the discarded card was a land)
        assertCounterCount(playerA, INFORMANT, CounterType.P1P1, 1);
        assertCounterCount(playerA, PURPOSE, CounterType.PLAN, 1);
    }

    @Test
    public void testSixthPlanCounterSacrificesAndCastsFree() {
        setStrictChooseMode(true);
        skipInitShuffling();
        addCard(Zone.BATTLEFIELD, playerA, PURPOSE);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.HAND, playerA, INFORMANT);
        addCard(Zone.HAND, playerA, "Plains");
        // library, top last: connive draws the top card, then four are exiled
        addCard(Zone.LIBRARY, playerA, "Island", 2);
        addCard(Zone.LIBRARY, playerA, "Divination");
        addCard(Zone.LIBRARY, playerA, "Island");
        addCard(Zone.LIBRARY, playerA, "Mountain"); // drawn by connive

        runCode("five plan counters", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) -> {
            Permanent purpose = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> PURPOSE.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            purpose.addCounters(CounterType.PLAN.createInstance(5), player.getId(), purpose.getAbilities().get(0), game);
        });
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, INFORMANT);
        setChoice(playerA, "Plains"); // connive discard
        setChoice(playerA, true); // cast Divination, the only castable spell among the four, for free

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, PURPOSE, 0);
        assertGraveyardCount(playerA, PURPOSE, 1);
        assertGraveyardCount(playerA, "Divination", 1);
        // Mountain (connive draw) + three exiled lands put into hand + two Divination draws
        assertHandCount(playerA, "Island", 3);
        assertHandCount(playerA, 1 + 3 + 2);
    }
}
