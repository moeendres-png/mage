package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.player.TestPlayer;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Heart-Shaped Herb {4}
 * Artifact
 * If a source an opponent controls would deal damage to you, prevent 1 of that damage.
 * {2}, {T}, Sacrifice this artifact: You may sacrifice a creature. If you do, return that card
 * to the battlefield under its owner's control with three +1/+1 counters on it and you become the monarch.
 *
 * @author commander-lab
 */
public class HeartShapedHerbTest extends CardTestPlayerBase {

    private static final String HERB = "Heart-Shaped Herb";

    @Test
    public void testOpponentsDamageToYouIsPreventedByOne() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, HERB);
        addCard(Zone.BATTLEFIELD, playerB, "Mountain");
        addCard(Zone.HAND, playerB, "Lightning Bolt");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerB, "Lightning Bolt", playerA);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerB, "Lightning Bolt", 1);
        assertLife(playerA, 18); // 3 of Lightning Bolt reduced by 1
    }

    @Test
    public void testYourOwnDamageSourceIsNotReduced() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, HERB);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        addCard(Zone.HAND, playerA, "Lightning Bolt");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Lightning Bolt", playerA);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertLife(playerA, 17); // full 3, own source is not affected
    }

    @Test
    public void testSacrificedCreatureReturnsWithThreeCountersAndYouBecomeMonarch() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, HERB);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}, Sacrifice {this}");
        setChoice(playerA, "Grizzly Bears");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, HERB, 1);
        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertCounterCount(playerA, "Grizzly Bears", CounterType.P1P1, 3);
        assertPowerToughness(playerA, "Grizzly Bears", 5, 5);
        Assert.assertEquals(playerA.getId(), currentGame.getMonarchId());
    }

    @Test
    public void testDecliningTheSacrificeGrantsNeitherCreatureNorCrown() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, HERB);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}, Sacrifice {this}");
        setChoice(playerA, TestPlayer.CHOICE_SKIP); // decline the "may sacrifice"

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, HERB, 1);
        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertCounterCount(playerA, "Grizzly Bears", CounterType.P1P1, 0);
        Assert.assertNull(currentGame.getMonarchId());
    }

    @Test
    public void testNoCreatureToSacrificeGrantsNoCrown() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, HERB);
        addCard(Zone.BATTLEFIELD, playerA, "Forest", 2);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{2}, {T}, Sacrifice {this}");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, HERB, 1);
        Assert.assertNull(currentGame.getMonarchId());
    }
}
