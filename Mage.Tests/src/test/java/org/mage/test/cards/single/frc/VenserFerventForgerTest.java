package org.mage.test.cards.single.frc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Venser, Fervent Forger {4}{R}{R} 5/3
 * Flash
 * When Venser enters, choose one --
 * * Copy target instant or sorcery spell an opponent controls twice. You may choose new targets for the copies.
 * * Create two tokens that are copies of target permanent an opponent controls. They gain haste. At the beginning
 *   of the next end step, sacrifice them.
 */
public class VenserFerventForgerTest extends CardTestPlayerBase {

    private static final String venser = "Venser, Fervent Forger";

    @Test
    public void testCopiesOpponentSpellTwice() {
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 6);
        addCard(Zone.HAND, playerA, venser);
        addCard(Zone.BATTLEFIELD, playerB, "Mountain");
        addCard(Zone.HAND, playerB, "Lightning Bolt");

        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Lightning Bolt", playerA);
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerA, venser);
        setModeChoice(playerA, "1");
        addTarget(playerA, "Lightning Bolt");
        setChoice(playerA, false); // keep the targets of the first copy
        setChoice(playerA, false); // keep the targets of the second copy
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, venser, 1);
        assertLife(playerA, 20 - 3 * 3); // the original and both copies hit the controller of Venser
    }

    @Test
    public void testCopyPermanentTwiceWithHasteAndSacrificeAtEnd() {
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 6);
        addCard(Zone.HAND, playerA, venser);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, venser);
        setModeChoice(playerA, "2");
        addTarget(playerA, "Grizzly Bears");
        attack(1, playerA, "Grizzly Bears");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.POSTCOMBAT_MAIN);
        execute();

        assertPermanentCount(playerA, "Grizzly Bears", 2);
        assertPermanentCount(playerB, "Grizzly Bears", 1);
        assertLife(playerB, 20 - 2); // one hasty copy attacked (the framework attacks with one creature per command)
    }

    @Test
    public void testTokensAreSacrificedAtTheNextEndStep() {
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 6);
        addCard(Zone.HAND, playerA, venser);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, venser);
        setModeChoice(playerA, "2");
        addTarget(playerA, "Grizzly Bears");
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        assertPermanentCount(playerA, venser, 1);
        assertPermanentCount(playerA, "Grizzly Bears", 0);
        assertPermanentCount(playerB, "Grizzly Bears", 1);
    }
}
