package org.mage.test.serverside.ws206;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * WS206 actual-card combat-damage matrix (current CR 510.1c-e, 702.19b).
 *
 * <p>Attackers: Alpine Grizzly (4/2, no trample), Colossal Dreadmaw (6/6 trample),
 * White Knight (2/2 first strike), Warren Instigator (1/1 double strike).
 * Blockers: Grizzly Bears (2/2), Silvercoat Lion (2/2), Fortress Crab (1/6),
 * Spectral Lynx (2/1 protection from green), Benalish Infantry (1/3 banding).
 */
public class WS206CombatDamageMatrixTest extends CardTestPlayerBase {

    // ---- 1. Non-trample free division (CR 510.1c): no lethal ordering ----

    @Test
    public void testNonTrampleAllToFirstBlocker() {
        addCard(Zone.BATTLEFIELD, playerA, "Alpine Grizzly"); // 4/2
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "Alpine Grizzly");
        block(1, playerB, "Grizzly Bears", "Alpine Grizzly");
        block(1, playerB, "Silvercoat Lion", "Alpine Grizzly");

        setChoiceAmount(playerA, 4, 0);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20); // blocked, no trample
        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertPermanentCount(playerB, "Silvercoat Lion", 1);
        assertDamageReceived(playerB, "Silvercoat Lion", 0);
    }

    @Test
    public void testNonTrampleAllToSecondBlocker() {
        addCard(Zone.BATTLEFIELD, playerA, "Alpine Grizzly"); // 4/2
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "Alpine Grizzly");
        block(1, playerB, "Grizzly Bears", "Alpine Grizzly");
        block(1, playerB, "Silvercoat Lion", "Alpine Grizzly");

        setChoiceAmount(playerA, 0, 4);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20);
        assertPermanentCount(playerB, "Grizzly Bears", 1);
        assertDamageReceived(playerB, "Grizzly Bears", 0);
        assertPermanentCount(playerB, "Silvercoat Lion", 0);
        assertGraveyardCount(playerB, "Silvercoat Lion", 1);
    }

    @Test
    public void testNonTrampleSplit() {
        addCard(Zone.BATTLEFIELD, playerA, "Alpine Grizzly"); // 4/2
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "Alpine Grizzly");
        block(1, playerB, "Grizzly Bears", "Alpine Grizzly");
        block(1, playerB, "Silvercoat Lion", "Alpine Grizzly");

        setChoiceAmount(playerA, 1, 3);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20);
        // 1 < 2: Bears survives with 1; 3 >= 2: Lion dies
        assertPermanentCount(playerB, "Grizzly Bears", 1);
        assertDamageReceived(playerB, "Grizzly Bears", 1);
        assertPermanentCount(playerB, "Silvercoat Lion", 0);
        assertGraveyardCount(playerB, "Silvercoat Lion", 1);
    }

    // ---- 2. Trample (CR 702.19b) ----

    @Test
    public void testTrampleLegalLethalEachPlusThrough() {
        addCard(Zone.BATTLEFIELD, playerA, "Colossal Dreadmaw"); // 6/6 trample
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "Colossal Dreadmaw");
        block(1, playerB, "Grizzly Bears", "Colossal Dreadmaw");
        block(1, playerB, "Silvercoat Lion", "Colossal Dreadmaw");

        setChoiceAmount(playerA, 2, 2); // 2 through

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 18);
        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertPermanentCount(playerB, "Silvercoat Lion", 0);
    }

    @Test
    public void testTrampleZeroThroughFreeDistribution() {
        // CR 702.19b last sentence: with no through-damage, no blocker needs lethal.
        addCard(Zone.BATTLEFIELD, playerA, "Colossal Dreadmaw"); // 6/6 trample
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "Colossal Dreadmaw");
        block(1, playerB, "Grizzly Bears", "Colossal Dreadmaw");
        block(1, playerB, "Silvercoat Lion", "Colossal Dreadmaw");

        setChoiceAmount(playerA, 6, 0); // 0 through, Lion below lethal: legal

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20);
        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertPermanentCount(playerB, "Silvercoat Lion", 1);
        assertDamageReceived(playerB, "Silvercoat Lion", 0);
    }

    // ---- 3. Already-marked damage reduces remaining lethal ----

    @Test
    public void testTrampleAlreadyMarkedDamage() {
        addCard(Zone.BATTLEFIELD, playerA, "Colossal Dreadmaw"); // 6/6 trample
        addCard(Zone.BATTLEFIELD, playerB, "Fortress Crab"); // 1/6
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerA, "Mountain", 2);
        addCard(Zone.HAND, playerA, "Shock", 2); // 2 damage each

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Shock", "Fortress Crab");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Shock", "Fortress Crab");
        // Crab has 4 marked, remaining lethal 2

        attack(1, playerA, "Colossal Dreadmaw");
        block(1, playerB, "Fortress Crab", "Colossal Dreadmaw");
        block(1, playerB, "Grizzly Bears", "Colossal Dreadmaw");

        setChoiceAmount(playerA, 2, 2); // 2 through; legal only because marked counts

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 18);
        assertPermanentCount(playerB, "Fortress Crab", 0); // 4 + 2 = 6 dies
        assertPermanentCount(playerB, "Grizzly Bears", 0);
    }

    // ---- 4. Protection must not lower lethal requirement ----

    @Test
    public void testTrampleProtectionStillRequiresLethal() {
        addCard(Zone.BATTLEFIELD, playerA, "Colossal Dreadmaw"); // 6/6 green trample
        addCard(Zone.BATTLEFIELD, playerB, "Spectral Lynx"); // 2/1 protection from green
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2

        attack(1, playerA, "Colossal Dreadmaw");
        block(1, playerB, "Spectral Lynx", "Colossal Dreadmaw");
        block(1, playerB, "Grizzly Bears", "Colossal Dreadmaw");

        // First attempt illegal (0 to Lynx with 3 through), then legal (1 to Lynx).
        // Note: 0+3 meets the dialogue totalMin (3) so it reaches the engine,
        // where per-blocker trample legality rejects it.
        setChoiceAmount(playerA, 0, 3, 1, 2);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        // Legal retry: 1 assigned to Lynx (prevented, 0 actual) + 2 to Bears + 3 through
        assertLife(playerB, 17);
        assertPermanentCount(playerB, "Spectral Lynx", 1);
        assertDamageReceived(playerB, "Spectral Lynx", 0);
        assertPermanentCount(playerB, "Grizzly Bears", 0);
    }

    // ---- 5. Deathtouch + trample: 1 is lethal ----

    @Test
    public void testTrampleDeathtouchMultiBlocker() {
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 2);
        addCard(Zone.BATTLEFIELD, playerA, "Colossal Dreadmaw"); // 6/6 trample
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2
        addCard(Zone.HAND, playerA, "Bladebrand"); // target gains deathtouch

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Bladebrand", "Colossal Dreadmaw");

        attack(1, playerA, "Colossal Dreadmaw");
        block(1, playerB, "Grizzly Bears", "Colossal Dreadmaw");
        block(1, playerB, "Silvercoat Lion", "Colossal Dreadmaw");

        setChoiceAmount(playerA, 1, 1); // 4 through; 1 is lethal via deathtouch

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 16);
        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertPermanentCount(playerB, "Silvercoat Lion", 0);
    }

    // ---- 6. First strike scoping with multiple blockers ----

    @Test
    public void testFirstStrikeMultiBlockerNoLeak() {
        addCard(Zone.BATTLEFIELD, playerA, "White Knight"); // 2/2 first strike
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "White Knight");
        block(1, playerB, "Grizzly Bears", "White Knight");
        block(1, playerB, "Silvercoat Lion", "White Knight");

        // First-strike step: all 2 to Bears (free division, no trample).
        setChoiceAmount(playerA, 2, 0);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        // Bears died in first step; Lion deals 2 to Knight in normal step; Knight dies too.
        assertLife(playerB, 20);
        assertPermanentCount(playerA, "White Knight", 0);
        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertPermanentCount(playerB, "Silvercoat Lion", 1);
    }

    // ---- 7. Double strike both steps with multiple blockers ----

    @Test
    public void testDoubleStrikeMultiBlockerBothSteps() {
        addCard(Zone.BATTLEFIELD, playerA, "Warren Instigator"); // 1/1 double strike
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Silvercoat Lion"); // 2/2

        attack(1, playerA, "Warren Instigator");
        block(1, playerB, "Grizzly Bears", "Warren Instigator");
        block(1, playerB, "Silvercoat Lion", "Warren Instigator");

        // First step 1 to Bears, second step 1 to Bears (Bears dies); Lion untouched.
        setChoiceAmount(playerA, 1, 0, 1, 0);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20);
        assertPermanentCount(playerB, "Grizzly Bears", 0);
        assertGraveyardCount(playerB, "Grizzly Bears", 1);
        assertPermanentCount(playerB, "Silvercoat Lion", 1);
        assertDamageReceived(playerB, "Silvercoat Lion", 0);
    }

    // ---- 8. Banding: defending player chooses attacker's damage (CR 702.22j) ----

    @Test
    public void testBandingDefenderChoosesVsTrample() {
        addCard(Zone.BATTLEFIELD, playerA, "Colossal Dreadmaw"); // 6/6 trample
        addCard(Zone.BATTLEFIELD, playerB, "Benalish Infantry"); // 1/3 banding
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears"); // 2/2

        attack(1, playerA, "Colossal Dreadmaw");
        block(1, playerB, "Benalish Infantry", "Colossal Dreadmaw");
        block(1, playerB, "Grizzly Bears", "Colossal Dreadmaw");

        // Banding blocker present: defending player (B) assigns the attacker's damage.
        setChoiceAmount(playerB, 3, 2); // 1 through

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 19);
        assertPermanentCount(playerB, "Benalish Infantry", 0);
        assertPermanentCount(playerB, "Grizzly Bears", 0);
    }

    // ---- 9. One blocker vs multiple attackers (CR 510.1d) ----

    @Test
    public void testBlockerVsMultipleAttackersFreeDivision() {
        addCard(Zone.BATTLEFIELD, playerA, "Grizzly Bears"); // 2/2
        addCard(Zone.BATTLEFIELD, playerA, "Silvercoat Lion"); // 2/2
        addCard(Zone.BATTLEFIELD, playerB, "Brave the Sands"); // can block an additional creature
        addCard(Zone.BATTLEFIELD, playerB, "Fortress Crab"); // 1/6

        attack(1, playerA, "Grizzly Bears");
        attack(1, playerA, "Silvercoat Lion");
        block(1, playerB, "Fortress Crab", "Grizzly Bears");
        block(1, playerB, "Fortress Crab", "Silvercoat Lion");

        // Crab (1 power) divides freely: all 1 to Bears.
        setChoiceAmount(playerB, 1, 0);

        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 20);
        assertDamageReceived(playerA, "Grizzly Bears", 1);
        assertDamageReceived(playerA, "Silvercoat Lion", 0);
        // Attackers deal 2 + 2 = 4 to the 1/6 Crab; it survives.
        assertPermanentCount(playerB, "Fortress Crab", 1);
        assertDamageReceived(playerB, "Fortress Crab", 4);
    }
}
