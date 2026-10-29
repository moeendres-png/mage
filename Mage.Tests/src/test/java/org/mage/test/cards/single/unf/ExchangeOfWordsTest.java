package org.mage.test.cards.single.unf;

import mage.abilities.keyword.FlyingAbility;
import mage.abilities.keyword.VigilanceAbility;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * Exchange of Words {1}{U}{U}
 * Enchantment
 * When this enchantment enters, choose two target creatures. For as long as this enchantment remains on the
 * battlefield, exchange the text boxes of those creatures.
 */
public class ExchangeOfWordsTest extends CardTestPlayerBase {

    private static final String exchange = "Exchange of Words";
    private static final String bears = "Grizzly Bears";
    private static final String angel = "Serra Angel"; // 4/4 flying, vigilance
    private static final String sorcerer = "Prodigal Sorcerer"; // {T}: deals 1 damage to any target

    @Test
    public void testAbilitiesChangeSidesWhileTheEnchantmentRemains() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 3);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, angel);
        addCard(Zone.HAND, playerA, exchange);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, exchange);
        addTarget(playerA, bears + "^" + angel);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();

        assertAbility(playerA, bears, FlyingAbility.getInstance(), true);
        assertAbility(playerA, bears, VigilanceAbility.getInstance(), true);
        assertAbility(playerB, angel, FlyingAbility.getInstance(), false);
        assertAbility(playerB, angel, VigilanceAbility.getInstance(), false);
        assertPowerToughness(playerA, bears, 2, 2); // only the text box moves, not power and toughness
        assertPowerToughness(playerB, angel, 4, 4);
    }

    @Test
    public void testActivatedAbilityMovesToTheOtherCreature() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 3);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerA, sorcerer);
        addCard(Zone.HAND, playerA, exchange);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, exchange);
        addTarget(playerA, bears + "^" + sorcerer);
        checkPlayableAbility("bears can ping", 1, PhaseStep.POSTCOMBAT_MAIN, playerA, "{T}: ", true); // Bears can ping
        activateAbility(1, PhaseStep.POSTCOMBAT_MAIN, playerA, "{T}: ", playerB);
        setStrictChooseMode(true);
        setStopAt(1, PhaseStep.END_TURN);
        execute();

        assertLife(playerB, 19);
        assertTapped(bears, true);
        assertTapped(sorcerer, false);
    }

    @Test
    public void testTextBoxesReturnWhenTheEnchantmentLeaves() {
        addCard(Zone.BATTLEFIELD, playerA, "Island", 3);
        addCard(Zone.BATTLEFIELD, playerA, bears);
        addCard(Zone.BATTLEFIELD, playerB, angel);
        addCard(Zone.BATTLEFIELD, playerB, "Plains", 2);
        addCard(Zone.HAND, playerB, "Disenchant");
        addCard(Zone.HAND, playerA, exchange);

        castSpell(1, PhaseStep.PRECOMBAT_MAIN, playerA, exchange);
        addTarget(playerA, bears + "^" + angel);
        castSpell(2, PhaseStep.PRECOMBAT_MAIN, playerB, "Disenchant", exchange);
        setStrictChooseMode(true);
        setStopAt(2, PhaseStep.BEGIN_COMBAT);
        execute();

        assertGraveyardCount(playerA, exchange, 1);
        assertAbility(playerA, bears, FlyingAbility.getInstance(), false);
        assertAbility(playerB, angel, FlyingAbility.getInstance(), true);
        assertAbility(playerB, angel, VigilanceAbility.getInstance(), true);
    }
}
