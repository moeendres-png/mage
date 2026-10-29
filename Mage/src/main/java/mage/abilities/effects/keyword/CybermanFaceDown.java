package mage.abilities.effects.keyword;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.effects.common.continuous.BecomesCybermanArtifactEffect;
import mage.abilities.effects.common.continuous.BecomesFaceDownCreatureEffect;
import mage.abilities.effects.common.continuous.BecomesFaceDownCreatureEffect.FaceDownType;
import mage.cards.Card;
import mage.constants.Duration;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Set;

/**
 * Doctor Who Cyberman cards: a card or permanent is face down and "It's a 2/2 Cyberman artifact creature."
 * It has no way to be turned face up (no morph, manifest or disguise cost).
 */
public final class CybermanFaceDown {

    private CybermanFaceDown() {
    }

    /**
     * Puts the cards onto the battlefield face down as 2/2 Cyberman artifact creatures under the
     * control of the given player.
     *
     * @return the permanents that entered the battlefield
     */
    public static List<Permanent> putOntoBattlefield(Game game, Ability source, Player player, Set<Card> cards, boolean tapped) {
        if (cards.isEmpty()) {
            return Collections.emptyList();
        }
        Ability faceDownSource = source.copy();
        faceDownSource.setWorksFaceDown(true);
        for (Card card : cards) {
            Card battlefieldCard = BecomesFaceDownCreatureEffect.findDefaultCardSideForFaceDown(game, card);
            // zcc + 1: the effects are set up before the card moves, as ManifestEffect does
            MageObjectReference reference = new MageObjectReference(battlefieldCard.getId(), battlefieldCard.getZoneChangeCounter(game) + 1, game);
            addEffects(game, faceDownSource, reference);
        }
        // the player's own controller of the ability is the controller of the new permanents
        player.moveCards(cards, Zone.BATTLEFIELD, source, game, tapped, true, false, null);
        List<Permanent> permanents = new ArrayList<>();
        for (Card card : cards) {
            Card battlefieldCard = BecomesFaceDownCreatureEffect.findDefaultCardSideForFaceDown(game, card);
            Permanent permanent = game.getPermanent(battlefieldCard.getId());
            if (permanent != null) {
                permanents.add(permanent);
            }
        }
        return permanents;
    }

    /**
     * Turns a face-up permanent face down. It becomes a 2/2 Cyberman artifact creature.
     */
    public static boolean turnFaceDown(Game game, Ability source, Permanent permanent) {
        if (permanent == null || permanent.isFaceDown(game)) {
            return false;
        }
        if (!permanent.turnFaceDown(source, game, source.getControllerId())) {
            return false;
        }
        MageObjectReference reference = new MageObjectReference(permanent.getId(), permanent.getZoneChangeCounter(game), game);
        addEffects(game, source, reference);
        return true;
    }

    private static void addEffects(Game game, Ability source, MageObjectReference reference) {
        game.addEffect(new BecomesFaceDownCreatureEffect(null, reference, Duration.Custom, FaceDownType.MANUAL), source);
        game.addEffect(new BecomesCybermanArtifactEffect(reference), source);
    }
}
