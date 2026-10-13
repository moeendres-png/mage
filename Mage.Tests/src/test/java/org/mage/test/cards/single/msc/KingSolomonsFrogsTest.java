package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * King Solomon's Frogs {3}{W}
 * Legendary Artifact
 * Flash
 * When King Solomon's Frogs enters, if you cast it, for each opponent, exile up to one target permanent
 * that player controls with mana value 3 or greater. For each permanent exiled this way, its controller
 * draws a card.
 * {3}, {T}, Exile King Solomon's Frogs: You become the monarch.
 *
 * @author commander-lab
 */
public class KingSolomonsFrogsTest extends CardTestPlayerBase {

    private static final String FROGS = "King Solomon's Frogs";

    @Test
    public void testCastExilesOpponentsPermanentAndThatOpponentDraws() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, FROGS);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.BATTLEFIELD, playerB, "Colossal Dreadmaw"); // mana value 6

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, FROGS);
        addTarget(playerA, "Colossal Dreadmaw");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, FROGS, 1);
        assertExileCount(playerB, "Colossal Dreadmaw", 1);
        assertGraveyardCount(playerB, "Colossal Dreadmaw", 0);
        assertHandCount(playerB, 1); // its controller draws a card
    }

    /**
     * Mana value 2 permanents never pass the filter, so the game must refuse to exile them.
     */
    @Test
    public void testManaValue2PermanentIsNotALegalTarget() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, FROGS);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // mana value 2

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, FROGS);
        addTarget(playerA, "Grizzly Bears"); // illegal, so the game can't use it

        setStopAt(1, PhaseStep.BEGIN_COMBAT);

        String error = null;
        try {
            execute();
        } catch (AssertionError e) {
            error = e.getMessage();
        }
        // the target def can only stay unused if the permanent was not a legal target
        Assert.assertNotNull("Mana value 2 permanent must be rejected as a target", error);
        Assert.assertTrue("Wrong rejection reason: " + error,
                error.contains("but not used") || error.contains("Missing TARGET def"));
        assertPermanentCount(playerB, "Grizzly Bears", 1);
        assertHandCount(playerB, 0);
    }

    @Test
    public void testOnlyTheBigPermanentOfTheOpponentIsExiled() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, FROGS);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.BATTLEFIELD, playerB, "Colossal Dreadmaw"); // mana value 6
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // mana value 2

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, FROGS);
        addTarget(playerA, "Colossal Dreadmaw");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertExileCount(playerB, "Colossal Dreadmaw", 1);
        assertPermanentCount(playerB, "Grizzly Bears", 1);
        assertHandCount(playerB, 1); // one permanent exiled, one card drawn
    }

    @Test
    public void testAlreadyOnTheBattlefieldNeverTriggers() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, FROGS); // never cast it
        addCard(Zone.BATTLEFIELD, playerB, "Colossal Dreadmaw");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, FROGS, 1);
        assertPermanentCount(playerB, "Colossal Dreadmaw", 1);
        assertHandCount(playerB, 0);
    }

    @Test
    public void testExilingItMakesYouMonarch() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, FROGS);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{3}, {T}, Exile {this}");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertExileCount(playerA, FROGS, 1);
        Assert.assertEquals(playerA.getId(), currentGame.getMonarchId());
    }

    @Test
    public void testExilingItTakesTheCrownFromTheCurrentMonarch() {
        setStrictChooseMode(true);
        addCard(Zone.BATTLEFIELD, playerA, FROGS);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 3);
        runCode("PlayerB is the monarch", 1, PhaseStep.UPKEEP, playerA,
                (info, player, game) -> game.setMonarchId(null, playerB.getId()));

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{3}, {T}, Exile {this}");

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertExileCount(playerA, FROGS, 1);
        Assert.assertEquals(playerA.getId(), currentGame.getMonarchId());
    }
}
