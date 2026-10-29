package org.mage.test.cards.single.who;

import mage.abilities.costs.mana.GenericManaCost;
import mage.abilities.keyword.WardAbility;
import mage.constants.PhaseStep;
import mage.constants.SubType;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Psychic Paper {2}
 * Artifact -- Equipment
 * As this Equipment becomes attached to a creature, choose a creature card name and a creature type.
 * Equipped creature has ward {1}, it can't be blocked, and its name and creature type are the last chosen
 * name and creature type.
 * Equip {2}
 */
public class PsychicPaperTest extends CardTestPlayerBase {

    private static final String paper = "Psychic Paper";
    private static final String bears = "Grizzly Bears";
    private static final String elves = "Llanowar Elves";

    @Test
    public void testEquippedCreatureTakesTheChosenNameTypeWardAndCannotBeBlocked() {
        addCard(Zone.BATTLEFIELD, playerA, paper);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, "Savannah Lions");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Equip {2}", bears);
        setChoice(playerA, elves);
        setChoice(playerA, "Elf");
        attack(1, playerA, elves);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, elves, 1);
        assertPermanentCount(playerA, bears, 0);
        assertSubtype(elves, SubType.ELF);
        assertNotSubtype(elves, SubType.BEAR);
        assertAbility(playerA, elves, new WardAbility(new GenericManaCost(1)), true);
        assertLife(playerB, 20 - 2); // unblockable although the Lions could block
        assertGraveyardCount(playerB, "Savannah Lions", 0);
    }

    @Test
    public void testItIsItselfAgainWhenTheEquipmentLeaves() {
        addCard(Zone.BATTLEFIELD, playerA, paper);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 2);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 2);
        addCard(Zone.HAND, playerB, "Disenchant");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Equip {2}", bears);
        setChoice(playerA, elves);
        setChoice(playerA, "Elf");
        castSpell(2, PhaseStep.UPKEEP, playerB, "Disenchant", paper);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertGraveyardCount(playerA, paper, 1);
        assertPermanentCount(playerA, bears, 1);
        assertPermanentCount(playerA, elves, 0);
        assertSubtype(bears, SubType.BEAR);
        assertNotSubtype(bears, SubType.ELF);
    }

    @Test
    public void testMovingItChoosesAgainAndTheLastChoiceCounts() {
        addCard(Zone.BATTLEFIELD, playerA, paper);
        addCard(Zone.BATTLEFIELD, playerA, "Plains", 4);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerA, "Serra Angel");

        activateAbility(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Equip {2}", bears);
        setChoice(playerA, elves);
        setChoice(playerA, "Elf");
        waitStackResolved(1, PhaseStep.PRECOMBAT_MAIN);
        activateAbility(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Equip {2}", "Serra Angel");
        setChoice(playerA, "Savannah Lions");
        setChoice(playerA, "Cat");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, bears, 1); // the first creature is itself again
        assertPermanentCount(playerA, elves, 0);
        assertPermanentCount(playerA, "Savannah Lions", 1); // the Angel carries the last chosen name
        assertPermanentCount(playerA, "Serra Angel", 0);
        assertSubtype("Savannah Lions", SubType.CAT);
        assertNotSubtype("Savannah Lions", SubType.ANGEL);
    }
}
