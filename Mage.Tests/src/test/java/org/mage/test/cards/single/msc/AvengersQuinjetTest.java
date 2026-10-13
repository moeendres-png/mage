package org.mage.test.cards.single.msc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * @author commander-lab
 */
public class AvengersQuinjetTest extends CardTestPlayerBase {

    private static final String QUINJET = "Avengers Quinjet";
    private static final String HERO = "Hercules, Olympian Hero";

    @Test
    public void testEntersPutsHeroFromHand() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, QUINJET);
        addCard(Zone.HAND, playerA, HERO);
        addCard(Zone.HAND, playerA, "Grizzly Bears"); // not a Hero: never put onto the battlefield
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 5);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, QUINJET);
        setModeChoice(playerA, "1");
        setChoice(playerA, true);
        setChoice(playerA, HERO);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertPermanentCount(playerA, HERO, 1);
        assertPermanentCount(playerA, "Grizzly Bears", 0);
    }

    @Test
    public void testEntersReturnsHeroFromGraveyard() {
        setStrictChooseMode(true);
        addCard(Zone.HAND, playerA, QUINJET);
        addCard(Zone.GRAVEYARD, playerA, HERO);
        addCard(Zone.BATTLEFIELD, playerA, "Wastes", 5);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, QUINJET);
        setModeChoice(playerA, "2");
        addTarget(playerA, HERO);

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertHandCount(playerA, HERO, 1);
    }
}
