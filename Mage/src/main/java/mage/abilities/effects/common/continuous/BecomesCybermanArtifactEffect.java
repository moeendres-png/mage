package mage.abilities.effects.common.continuous;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.effects.ContinuousEffectImpl;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Layer;
import mage.constants.Outcome;
import mage.constants.SubLayer;
import mage.constants.SubType;
import mage.game.Game;
import mage.game.permanent.Permanent;

/**
 * "It's a 2/2 Cyberman artifact creature." for a permanent that was turned face down by a Doctor Who
 * Cyberman card. The 2/2 face-down creature itself comes from BecomesFaceDownCreatureEffect (layer 1b);
 * this effect adds the artifact type and the Cyberman subtype on top of it (layer 4) for as long as the
 * permanent stays face down.
 */
public class BecomesCybermanArtifactEffect extends ContinuousEffectImpl {

    private final MageObjectReference reference;

    public BecomesCybermanArtifactEffect(MageObjectReference reference) {
        super(Duration.Custom, Layer.TypeChangingEffects_4, SubLayer.NA, Outcome.Benefit);
        this.reference = reference;
        this.staticText = "It's a 2/2 Cyberman artifact creature";
    }

    protected BecomesCybermanArtifactEffect(final BecomesCybermanArtifactEffect effect) {
        super(effect);
        this.reference = effect.reference;
    }

    @Override
    public BecomesCybermanArtifactEffect copy() {
        return new BecomesCybermanArtifactEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent permanent = reference.getPermanent(game);
        if (permanent == null || !permanent.isFaceDown(game)) {
            discard();
            return false;
        }
        permanent.addCardType(game, CardType.ARTIFACT);
        permanent.addSubType(game, SubType.CYBERMAN);
        return true;
    }
}
