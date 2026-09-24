package org.mage.test.serverside.rg07;

import mage.abilities.ActivatedAbility;
import mage.cards.Card;
import mage.constants.PhaseStep;
import mage.constants.Zone;
import mage.game.Game;
import mage.players.Player;
import org.junit.Assert;
import org.junit.Test;
import org.mage.test.serverside.base.CardTestPlayerBase;

/**
 * RG-07 baseline reproducer for exact-N target legal-action offering.
 */
public class RG07HexPlayableBaselineTest extends CardTestPlayerBase {

    private static final String HEX = "Hex";

    private static boolean isSpellOffered(Game game, Player player, String cardName) {
        for (ActivatedAbility ability : player.getPlayable(game, false)) {
            Card source = game.getCard(ability.getSourceId());
            if (source != null && cardName.equals(source.getName())) {
                return true;
            }
        }
        return false;
    }

    private void configureHexWithCreatureCount(int creatures) {
        addCard(Zone.HAND, playerA, HEX, 1);
        addCard(Zone.BATTLEFIELD, playerA, "Swamp", 6);
        addCard(Zone.BATTLEFIELD, playerB, "Grizzly Bears", creatures);
    }

    @Test
    public void hexNotOfferedWithFiveLegalCreatures() {
        configureHexWithCreatureCount(5);

        runCode("Hex offer with five targets", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                Assert.assertFalse("Hex must not be offered with only five legal creature targets",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void hexOfferedWithExactlySixLegalCreatures() {
        configureHexWithCreatureCount(6);

        runCode("Hex offer with six targets", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                Assert.assertTrue("Hex must be offered with exactly six legal creature targets",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }

    @Test
    public void hexOfferedWithSevenLegalCreatures() {
        configureHexWithCreatureCount(7);

        runCode("Hex offer with seven targets", 1, PhaseStep.PRECOMBAT_MAIN, playerA, (info, player, game) ->
                Assert.assertTrue("Hex must be offered when more than six legal creature targets exist",
                        isSpellOffered(game, player, HEX)));

        setStopAt(1, PhaseStep.BEGIN_COMBAT);
        execute();
    }
}
