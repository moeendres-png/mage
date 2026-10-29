package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * The Pandorica {2}{W}
 * Legendary Artifact
 * You may choose not to untap The Pandorica during your untap step.
 * {1}{W}, {T}: Untap another target nonland permanent, then it phases out. It can't phase in for as long as
 * The Pandorica remains tapped. When The Pandorica becomes untapped or leaves the battlefield, that permanent
 * phases in. Activate only as a sorcery.
 */
public class ThePandoricaTest extends CardTestPlayerBase {

    private static final String pandorica = "The Pandorica";
    private static final String lions = "Savannah Lions";
    private static final String ability = "{1}{W}, {T}: Untap another target nonland permanent";

    @Test
    public void testItStaysPhasedOutWhileTappedAndPhasesInWhenUntapped() {
        addCard(Zone.BATTLEFIELD, playerA, pandorica);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerB, lions);

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, ability, lions);
        // turn 2: the Lions' controller untaps, they would phase in now
        checkPermanentCount("still out on turn 2", 2, PhaseStep.PRECOMBAT_MAIN, playerB, lions, 0);
        setChoice(playerA, false); // turn 3 untap step: keep The Pandorica tapped
        // turn 4: B untaps again, still out
        checkPermanentCount("still out on turn 4", 4, PhaseStep.PRECOMBAT_MAIN, playerB, lions, 0);
        checkGraveyardCount("not dead", 4, PhaseStep.PRECOMBAT_MAIN, playerB, lions, 0);
        setChoice(playerA, true); // turn 5 untap step: untap it
        setStrictChooseMode(true);

        setStopAt(5, PhaseStep.PRECOMBAT_MAIN);
        execute();
        assertTapped(pandorica, false);
        assertPermanentCount(playerB, lions, 1);
    }

    @Test
    public void testItPhasesInWhenThePandoricaLeavesTheBattlefield() {
        addCard(Zone.BATTLEFIELD, playerA, pandorica);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerB, lions);
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 2);
        addCard(Zone.HAND, playerB, "Disenchant");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, ability, lions);
        castSpell(2, PhaseStep.UPKEEP, playerB, "Disenchant", pandorica);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerA, pandorica, 1);
        assertPermanentCount(playerB, lions, 1);
    }

    @Test
    public void testTheTargetIsUntappedBeforeItPhasesOut() {
        addCard(Zone.BATTLEFIELD, playerA, pandorica);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears");
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 2);
        addCard(Zone.HAND, playerB, "Disenchant");

        attack(1, playerA, "Grizzly Bears");
        activateAbility(1, PhaseStep.POSTCOMBAT_MAIN, playerA, ability, "Grizzly Bears");
        castSpell(2, PhaseStep.UPKEEP, playerB, "Disenchant", pandorica);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertPermanentCount(playerA, "Grizzly Bears", 1);
        assertTapped("Grizzly Bears", false);
    }

    @Test
    public void testItCannotTargetItselfOrALand() {
        addCard(Zone.BATTLEFIELD, playerA, pandorica);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);

        // no legal target at all: the ability is not offered
        checkPlayableAbility("no legal target", 1, PhaseStep.PRECOMBAT_MAIN, playerA, ability, false);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
