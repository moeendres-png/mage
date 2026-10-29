package org.mage.test.cards.single.mkc;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Eye of Duskmantle {5}{B}{B}
 * Creature -- Eye 3/8
 * Flying, lifelink
 * You may play lands and cast spells from among cards in your graveyard you've surveilled this turn.
 * If you cast a spell this way, you pay life equal to its mana value rather than paying its mana cost.
 */
public class EyeOfDuskmantleTest extends CardTestPlayerBase {

    private static final String eye = "Eye of Duskmantle";
    private static final String erasure = "Thought Erasure"; // {U}{B} sorcery: target opponent discards a card. Surveil 1.
    private static final String bolt = "Lightning Bolt";

    @Test
    public void testSurveilledSpellIsCastForLifeEqualToItsManaValue() {
        addCard(Zone.BATTLEFIELD, playerA, eye);
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp");
        addCard(Zone.HAND, playerA, erasure);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, bolt);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, erasure, playerB);
        addTarget(playerA, bolt); // surveil: put into the graveyard
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, bolt, playerB);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertGraveyardCount(playerA, bolt, 1); // resolved, so it is back in the graveyard
        assertLife(playerB, 17);
        assertLife(playerA, 19); // paid 1 life, no mana
    }

    @Test
    public void testSurveilledLandCanBePlayed() {
        addCard(Zone.BATTLEFIELD, playerA, eye);
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp");
        addCard(Zone.HAND, playerA, erasure);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Forest");

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, erasure, playerB);
        addTarget(playerA, "Forest");
        playLand(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Forest");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertPermanentCount(playerA, "Forest", 1);
        assertGraveyardCount(playerA, "Forest", 0);
    }

    @Test
    public void testOtherGraveyardCardsAreNotAvailable() {
        addCard(Zone.BATTLEFIELD, playerA, eye);
        addCard(Zone.GRAVEYARD, playerA, bolt);

        checkPlayableAbility("not surveilled", 1, PhaseStep.PRECOMBAT_MAIN, playerA, "Cast " + bolt, false);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();
    }

    @Test
    public void testPermissionEndsWithTheTurn() {
        addCard(Zone.BATTLEFIELD, playerA, eye);
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp");
        addCard(Zone.HAND, playerA, erasure);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, bolt);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, erasure, playerB);
        addTarget(playerA, bolt); // surveil: put into the graveyard
        checkPlayableAbility("same turn", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Cast " + bolt, true);
        checkPlayableAbility("next turn", 2, PhaseStep.UPKEEP, playerA, "Cast " + bolt, false);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.DRAW);
        execute();
    }

    @Test
    public void testNeedsEnoughLife() {
        addCard(Zone.BATTLEFIELD, playerA, eye);
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.BATTLEFIELD, playerA, "Swamp");
        addCard(Zone.HAND, playerA, erasure);
        removeAllCardsFromLibrary(playerA);
        addCard(Zone.LIBRARY, playerA, "Wrath of God"); // mana value 4

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, erasure, playerB);
        addTarget(playerA, "Wrath of God");
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Wrath of God");
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertGraveyardCount(playerA, "Wrath of God", 1);
        assertGraveyardCount(playerA, eye, 1); // wrath destroyed the Eye, 4 life paid
        assertLife(playerA, 16);
    }
}
