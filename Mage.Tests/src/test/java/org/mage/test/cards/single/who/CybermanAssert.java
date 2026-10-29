package org.mage.test.cards.single.who;

import mage.constants.SubType;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import org.junit.Assert;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Checks for the face-down "2/2 Cyberman artifact creatures" of the Doctor Who Cyberman cards.
 */
final class CybermanAssert {

    private CybermanAssert() {
    }

    static List<Permanent> faceDown(Game game, Player player) {
        return game.getBattlefield().getAllActivePermanents(player.getId()).stream()
                .filter(permanent -> permanent.isFaceDown(game))
                .collect(Collectors.toList());
    }

    /**
     * The player controls exactly this many face-down permanents and every one is a 2/2 Cyberman artifact creature.
     */
    static void assertCybermen(Game game, Player player, int count) {
        List<Permanent> permanents = faceDown(game, player);
        Assert.assertEquals("face-down permanents of " + player.getName(), count, permanents.size());
        for (Permanent permanent : permanents) {
            Assert.assertTrue("is a creature", permanent.isCreature(game));
            Assert.assertTrue("is an artifact", permanent.isArtifact(game));
            Assert.assertTrue("is a Cyberman", permanent.hasSubtype(SubType.CYBERMAN, game));
            Assert.assertEquals("base power", 2, permanent.getPower().getModifiedBaseValue());
            Assert.assertEquals("base toughness", 2, permanent.getToughness().getModifiedBaseValue());
        }
    }
}
