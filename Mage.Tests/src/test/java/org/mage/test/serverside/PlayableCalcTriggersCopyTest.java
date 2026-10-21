package org.mage.test.serverside;

import mage.abilities.TriggeredAbilities;
import mage.abilities.TriggeredAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.Game;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * A playable calculation copy copies the triggers of its parent on first use instead of up
 * front (GameState#triggers). It must still see the triggers its parent had when it was made,
 * in the same order, and nothing it does may reach back to the parent or to a sibling copy.
 */
public class PlayableCalcTriggersCopyTest extends CardTestPlayerBase {

    private static List<String> describe(TriggeredAbilities triggers) {
        List<String> res = new ArrayList<>();
        for (Map.Entry<String, TriggeredAbility> entry : triggers.entrySet()) {
            res.add(entry.getKey() + " | " + entry.getValue().getRule());
        }
        return res;
    }

    private void setUpBattlefield() {
        addCard(Zone.BATTLEFIELD, playerA, "Soul Warden");
        addCard(Zone.BATTLEFIELD, playerA, "Sylvan Library");
        addCard(Zone.BATTLEFIELD, playerB, "Soul Warden");
        setStopAt(1, PhaseStep.PRECOMBAT_MAIN);
        execute();
    }

    @Test
    public void copyHasTheTriggersOfItsParentInTheSameOrder() {
        setUpBattlefield();

        TriggeredAbilities parent = currentGame.getState().getTriggers();
        Assert.assertTrue("the test needs triggers to compare", parent.size() >= 3);

        Game copy = currentGame.createSimulationForPlayableCalc();
        TriggeredAbilities copied = copy.getState().getTriggers();

        Assert.assertNotSame(parent, copied);
        Assert.assertEquals(describe(parent), describe(copied));
        for (Map.Entry<String, TriggeredAbility> entry : parent.entrySet()) {
            Assert.assertNotSame(entry.getValue(), copied.get(entry.getKey()));
        }
    }

    @Test
    public void copyOfAnUnreadCopyIsIndependentOfParentAndSibling() {
        setUpBattlefield();

        List<String> before = describe(currentGame.getState().getTriggers());

        Game first = currentGame.createSimulationForPlayableCalc();
        // the first copy has not read its triggers when the second one is made from it
        Game second = first.createSimulationForPlayableCalc();
        Game third = currentGame.createSimulationForPlayableCalc();

        TriggeredAbilities viaSecond = second.getState().getTriggers();
        Assert.assertEquals(before, describe(viaSecond));
        viaSecond.clear();

        Assert.assertEquals(before, describe(currentGame.getState().getTriggers()));
        Assert.assertEquals(before, describe(first.getState().getTriggers()));
        Assert.assertEquals(before, describe(third.getState().getTriggers()));
        Assert.assertNotSame(first.getState().getTriggers(), third.getState().getTriggers());
    }

    @Test
    public void ordinaryCopyIsTakenUpFront() {
        setUpBattlefield();

        // an ordinary copy (not a playable calculation) copies up front, as it always did
        Game eager = currentGame.copy();
        List<String> before = describe(currentGame.getState().getTriggers());
        currentGame.getState().getTriggers().clear();

        Assert.assertEquals(before, describe(eager.getState().getTriggers()));
    }
}
