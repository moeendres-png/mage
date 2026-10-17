package org.mage.test.cards.single.sos;

import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.permanent.Permanent;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * The seven prepare creatures that the Secrets of Strixhaven set file used to hide in its
 * {@code unfinished} list: each one is now registered, castable and becomes prepared.
 *
 * @author commander-lab
 */
public class EnabledPrepareCardsTest extends CardTestPlayerBase {

    private void assertPrepared(String name, int turn, PhaseStep step, boolean expected) {
        runCode(name + " prepared=" + expected, turn, step, playerA, (info, player, game) -> {
            Permanent permanent = game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                    .filter(p -> name.equals(p.getName())).findFirst().orElseThrow(AssertionError::new);
            Assert.assertEquals(info, expected, permanent.isPrepared());
        });
    }

    private void castEntersPrepared(String name, String land, int lands) {
        addCard(Zone.HAND, playerA, name);
        addCard(Zone.BATTLEFIELD, playerA, land, lands);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, name);
        assertPrepared(name, 1, PhaseStep.BEGIN_COMBAT, true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
        assertPermanentCount(playerA, name, 1);
    }

    @Test
    public void testBlazingFiresingerEntersPrepared() {
        castEntersPrepared("Blazing Firesinger", "Mountain", 3);
    }

    @Test
    public void testCheerfulOsteomancerEntersPrepared() {
        castEntersPrepared("Cheerful Osteomancer", "Swamp", 4);
    }

    @Test
    public void testGoblinGlasswrightEntersPrepared() {
        castEntersPrepared("Goblin Glasswright", "Mountain", 2);
    }

    @Test
    public void testStudiousFirstYearEntersPrepared() {
        castEntersPrepared("Studious First-Year", "Forest", 1);
    }

    @Test
    public void testSanarEntersPrepared() {
        addCard(Zone.HAND, playerA, "Sanar, Unfinished Genius");
        addCard(Zone.BATTLEFIELD, playerA, "Island");
        addCard(Zone.BATTLEFIELD, playerA, "Mountain");
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Sanar, Unfinished Genius");
        assertPrepared("Sanar, Unfinished Genius", 1, PhaseStep.BEGIN_COMBAT, true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
        assertPermanentCount(playerA, "Sanar, Unfinished Genius", 1);
    }

    @Test
    public void testSpellbookSeekerPreparedCopyCanBeCast() {
        addCard(Zone.HAND, playerA, "Spellbook Seeker");
        addCard(Zone.BATTLEFIELD, playerA, "Island", 5);
        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Spellbook Seeker");
        assertPrepared("Spellbook Seeker", 1, PhaseStep.BEGIN_COMBAT, true);
        castSpell(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "Careful Study");
        assertPrepared("Spellbook Seeker", 1, PhaseStep.END_TURN, false);
        setStopAt(1, PhaseStep.END_TURN);
        execute();
        assertPermanentCount(playerA, "Spellbook Seeker", 1);
        // Careful Study: draw two, discard one
        assertHandCount(playerA, 1);
    }

    @Test
    public void testTamBecomesPreparedOnLandfall() {
        addCard(Zone.BATTLEFIELD, playerA, "Tam, Observant Sequencer");
        addCard(Zone.HAND, playerA, "Forest");
        assertPrepared("Tam, Observant Sequencer", 1, PhaseStep.UPKEEP, false);
        playLand(1, PhaseStep.PRECOMBAT_MAIN, playerA, "Forest");
        assertPrepared("Tam, Observant Sequencer", 1, PhaseStep.BEGIN_COMBAT, true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
