package org.mage.test.cards.single.who;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * River Song's Diary {3}
 * Artifact -- Book
 * Imprint -- Whenever a player casts an instant or sorcery spell from their hand, exile it instead of putting it
 * into a graveyard as it resolves.
 * At the beginning of your upkeep, if there are four or more cards exiled with this artifact, choose one of them
 * at random. You may cast it without paying its mana cost.
 */
public class RiverSongsDiaryTest extends CardTestPlayerBase {

    private static final String diary = "River Song's Diary";
    private static final String bolt = "Lightning Bolt";

    @Test
    public void testTheFourthExiledCardEnablesTheUpkeepCast() {
        addCard(Zone.BATTLEFIELD, playerA, diary);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 4);
        addCard(Zone.HAND, playerA, bolt, 4);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, bolt, playerB);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, bolt, playerB);
        castSpell(1, PhaseStep.END_TURN, playerA, bolt, playerB);
        castSpell(1, PhaseStep.END_TURN, playerA, bolt, playerB);
        // turn 3 upkeep: four cards are exiled with the Diary, one of them is cast for free
        setChoice(playerA, true);
        addTarget(playerA, playerB);
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertLife(playerB, 20 - 4 * 3 - 3);
        assertExileCount(playerA, bolt, 3); // one was cast from exile (not from hand) and went to the graveyard
        assertGraveyardCount(playerA, bolt, 1);
    }

    @Test
    public void testThreeExiledCardsDoNotTrigger() {
        addCard(Zone.BATTLEFIELD, playerA, diary);
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 3);
        addCard(Zone.HAND, playerA, bolt, 3);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, bolt, playerB);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, bolt, playerB);
        castSpell(1, PhaseStep.END_TURN, playerA, bolt, playerB);
        // no choice is defined for turn 3: nothing may trigger
        setStrictChooseMode(true);
        setStopAt(3, PhaseStep.PRECOMBAT_MAIN);
        execute();

        assertExileCount(playerA, bolt, 3);
        assertGraveyardCount(playerA, bolt, 0);
        assertLife(playerB, 20 - 9);
    }

    @Test
    public void testAnInstantFromHandOfTheOpponentIsImprintedToo() {
        addCard(Zone.BATTLEFIELD, playerA, diary);
        addCard(Zone.BATTLEFIELD, playerB, "Mountain");
        addCard(Zone.HAND, playerB, bolt);

        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, bolt, playerA);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertExileCount(playerB, bolt, 1);
        assertGraveyardCount(playerB, bolt, 0);
    }
}
