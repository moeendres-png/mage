package org.mage.test.cards.single.dsc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.counters.CounterType;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Winter, Cynical Opportunist {2}{B}{G} 2/5
 * Deathtouch
 * Whenever Winter attacks, mill three cards.
 * Delirium -- At the beginning of your end step, you may exile any number of cards from your graveyard with four or
 * more card types among them. If you do, put a permanent card from among them onto the battlefield with a finality counter on it.
 */
public class WinterCynicalOpportunistTest extends CardTestPlayerBase {

    private static final String winter = "Winter, Cynical Opportunist";

    @Test
    public void testFourCardTypesReturnPermanentWithFinalityCounter() {
        addCard(Zone.BATTLEFIELD, playerA, winter);
        addCard(Zone.GRAVEYARD, playerA, "Grizzly Bears"); // creature
        addCard(Zone.GRAVEYARD, playerA, "Lightning Bolt"); // instant
        addCard(Zone.GRAVEYARD, playerA, "Forest"); // land
        addCard(Zone.GRAVEYARD, playerA, "Sol Ring"); // artifact

        setChoice(playerA, true);
        addTarget(playerA, "Grizzly Bears^Lightning Bolt^Forest^Sol Ring"); // cards to exile
        addTarget(playerA, "Sol Ring"); // permanent to return
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        assertPermanentCount(playerA, "Sol Ring", 1);
        assertCounterCount(playerA, "Sol Ring", CounterType.FINALITY, 1);
        assertExileCount(playerA, "Grizzly Bears", 1);
        assertExileCount(playerA, "Lightning Bolt", 1);
        assertExileCount(playerA, "Forest", 1);
        assertGraveyardCount(playerA, 0);
    }

    @Test
    public void testThreeCardTypesDoNothing() {
        addCard(Zone.BATTLEFIELD, playerA, winter);
        addCard(Zone.GRAVEYARD, playerA, "Grizzly Bears");
        addCard(Zone.GRAVEYARD, playerA, "Lightning Bolt");
        addCard(Zone.GRAVEYARD, playerA, "Forest");

        setChoice(playerA, true);
        addTarget(playerA, "Grizzly Bears^Lightning Bolt^Forest");
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        assertGraveyardCount(playerA, 3);
        assertPermanentCount(playerA, "Grizzly Bears", 0);
    }

    @Test
    public void testDecliningLeavesGraveyardAlone() {
        addCard(Zone.BATTLEFIELD, playerA, winter);
        addCard(Zone.GRAVEYARD, playerA, "Grizzly Bears");
        addCard(Zone.GRAVEYARD, playerA, "Lightning Bolt");
        addCard(Zone.GRAVEYARD, playerA, "Forest");
        addCard(Zone.GRAVEYARD, playerA, "Sol Ring");

        setChoice(playerA, false);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.UPKEEP);
        execute();

        assertGraveyardCount(playerA, 4);
        assertPermanentCount(playerA, "Sol Ring", 0);
    }
}
