package org.mage.test.cards.single.tdc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestCommander4Players;

/**
 * Protector of the Wastes
 * {4}{W}{W}
 * Creature - Dragon
 * Flying
 * When this creature enters or becomes monstrous, exile up to two target artifacts and/or enchantments
 * controlled by different players.
 * {4}{W}: Monstrosity 3.
 */
public class ProtectorOfTheWastesTest extends CardTestCommander4Players {

    private static final String protector = "Protector of the Wastes";
    private static final String fountain = "Fountain of Youth";
    private static final String anthem = "Glorious Anthem";
    private static final String screams = "Screams from Within";
    private static final String lion = "Silvercoat Lion";
    private static final String giant = "Hill Giant";

    @Test
    public void testEntersExilesTargetsOfDifferentPlayers() {
        setStrictChooseMode(true);

        addCard(Zone.HAND, playerA, protector);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 6);
        addCard(Zone.BATTLEFIELD, playerB, fountain);
        addCard(Zone.BATTLEFIELD, playerC, anthem);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, protector);
        addTarget(playerA, fountain);
        addTarget(playerA, anthem);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, protector, 1);
        assertExileCount(playerB, fountain, 1);
        assertExileCount(playerC, anthem, 1);
    }

    @Test
    public void testBecomesMonstrousExilesTargets() {
        setStrictChooseMode(true);

        addCard(Zone.BATTLEFIELD, playerA, protector);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 5);
        addCard(Zone.BATTLEFIELD, playerB, fountain);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{4}{W}: Monstrosity 3");
        addTarget(playerA, fountain);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertCounterCount(playerA, protector, mage.counters.CounterType.P1P1, 3);
        assertExileCount(playerB, fountain, 1);
    }

    @Test
    public void testAuraReturningWithoutSourceDoesNotBreakTheTrigger() {
        // Screams from Within returns to the battlefield without a source ability (AuraReplacementEffect);
        // the enters event then has no source id, which used to throw in the trigger check
        setStrictChooseMode(true);

        addCard(Zone.HAND, playerA, screams);
        addCard(Zone.HAND, playerA, "Doom Blade");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 5);
        addCard(Zone.BATTLEFIELD, playerA, lion);
        addCard(Zone.BATTLEFIELD, playerA, giant);
        addCard(Zone.BATTLEFIELD, playerB, protector);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, screams, lion);
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Doom Blade", lion);
        setChoice(playerA, giant); // what the returning Aura attaches to, big enough to survive its -1/-1

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, lion, 1);
        assertPermanentCount(playerA, screams, 1);
        assertPermanentCount(playerB, protector, 1);
    }
}
