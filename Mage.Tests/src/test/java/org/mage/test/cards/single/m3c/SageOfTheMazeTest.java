package org.mage.test.cards.single.m3c;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Sage of the Maze {2}{G}
 * Creature -- Elf Wizard 1/3
 * {T}: Add two mana in any combination of colors.
 * {T}: Until end of turn, target land you control becomes an X/X Citizen creature with haste in addition to its
 * other types, where X is twice the number of Gates you control. Activate only as a sorcery.
 * Tap an untapped Gate you control: Untap Sage of the Maze.
 */
public class SageOfTheMazeTest extends CardTestPlayerBase {

    private static final String sage = "Sage of the Maze";
    private static final String untap = "Tap an untapped Gate you control: Untap";

    @Test
    public void testUntapIsOfferedWithAnUntappedGate() {
        addCard(Zone.BATTLEFIELD, playerA, sage, 1, true);
        addCard(Zone.BATTLEFIELD, playerA, "Azorius Guildgate");

        checkPlayableAbility("untapped gate", 1, PhaseStep.PRECOMBAT_MAIN, playerA, untap, true);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void testUntapIsNotOfferedWhenEveryGateIsTapped() {
        addCard(Zone.BATTLEFIELD, playerA, sage, 1, true);
        addCard(Zone.BATTLEFIELD, playerA, "Azorius Guildgate");
        addCard(Zone.BATTLEFIELD, playerA, "Island"); // untapped, but no Gate

        activateManaAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "{T}: Add {W}"); // taps the only Gate
        checkPlayableAbility("only a tapped gate", 1, PhaseStep.PRECOMBAT_MAIN, playerA, untap, false);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void testUntapIsNotOfferedWithoutAnyGate() {
        addCard(Zone.BATTLEFIELD, playerA, sage, 1, true);
        addCard(Zone.BATTLEFIELD, playerA, "Island");

        checkPlayableAbility("no gate", 1, PhaseStep.PRECOMBAT_MAIN, playerA, untap, false);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void testTappingTheGateUntapsTheSage() {
        addCard(Zone.BATTLEFIELD, playerA, sage, 1, true);
        addCard(Zone.BATTLEFIELD, playerA, "Azorius Guildgate");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, untap);
        setChoice(playerA, "Azorius Guildgate");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertTapped(sage, false);
        assertTapped("Azorius Guildgate", true);
    }
}
