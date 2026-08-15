package mage.abilities.effects.common;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.effects.AsThoughEffectImpl;
import mage.abilities.effects.OneShotEffect;
import mage.cards.Card;
import mage.cards.PrepareCard;
import mage.constants.AsThoughEffectType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.util.CardUtil;

import java.util.UUID;

/**
 * @author TheElk801
 */
public class BecomePreparedSourceEffect extends OneShotEffect {

    public BecomePreparedSourceEffect() {
        super(Outcome.Benefit);
        staticText = "{this} becomes prepared";
    }

    private BecomePreparedSourceEffect(final BecomePreparedSourceEffect effect) {
        super(effect);
    }

    @Override
    public BecomePreparedSourceEffect copy() {
        return new BecomePreparedSourceEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent permanent = source.getSourcePermanentIfItStillExists(game);
        if (permanent == null) {
            return false;
        }

        // A permanent that is already prepared can't become prepared again
        // and must not create another prepare spell copy.
        if (permanent.isPrepared()) {
            return true;
        }

        if (!(permanent.getMainCard() instanceof PrepareCard)) {
            return false;
        }

        Player controller = game.getPlayer(permanent.getControllerId());
        if (controller == null) {
            return false;
        }

        PrepareCard prepareCard = (PrepareCard) permanent.getMainCard();

        Card spellCopy = game.copyCard(
                prepareCard.getSpellCard(),
                source,
                permanent.getControllerId()
        );

        controller.moveCardsToExile(
                spellCopy,
                source,
                game,
                true,
                CardUtil.getExileZoneId(game, source),
                CardUtil.getSourceIdName(game, source) + " prepare spell"
        );

        if (!Zone.EXILED.equals(game.getState().getZone(spellCopy.getId()))) {
            return false;
        }

        game.getState().setValue(
                PrepareCard.getPrepareCopyKey(spellCopy.getId()),
                new MageObjectReference(permanent, game)
        );

        permanent.setPrepared(true, game);

        // Allow exactly this prepare-spell copy to be cast from exile.
        // Eligibility is determined dynamically from the current controller
        // of the linked prepared permanent.
        game.addEffect(
                new CastPreparedSpellFromExileEffect(spellCopy.getId()),
                source
        );

        return true;
    }
}

class CastPreparedSpellFromExileEffect extends AsThoughEffectImpl {

    private final UUID spellCopyId;

    CastPreparedSpellFromExileEffect(UUID spellCopyId) {
        super(
                AsThoughEffectType.CAST_FROM_NOT_OWN_HAND_ZONE,
                Duration.Custom,
                Outcome.Benefit
        );
        this.spellCopyId = spellCopyId;
        staticText = "The current controller of the prepared permanent may cast its prepare spell copy from exile";
    }

    private CastPreparedSpellFromExileEffect(
            final CastPreparedSpellFromExileEffect effect
    ) {
        super(effect);
        this.spellCopyId = effect.spellCopyId;
    }

    @Override
    public CastPreparedSpellFromExileEffect copy() {
        return new CastPreparedSpellFromExileEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        return true;
    }

    @Override
    public boolean applies(
            UUID objectId,
            Ability source,
            UUID affectedControllerId,
            Game game
    ) {
        if (!spellCopyId.equals(objectId)) {
            return false;
        }

        Object prepareRef = game.getState().getValue(
                PrepareCard.getPrepareCopyKey(spellCopyId)
        );

        if (!(prepareRef instanceof MageObjectReference)) {
            discard();
            return false;
        }

        Permanent preparedPermanent =
                ((MageObjectReference) prepareRef).getPermanent(game);

        if (preparedPermanent == null || !preparedPermanent.isPrepared()) {
            discard();
            return false;
        }

        if (!Zone.EXILED.equals(game.getState().getZone(spellCopyId))) {
            discard();
            return false;
        }

        return preparedPermanent
                .getControllerId()
                .equals(affectedControllerId);
    }
}
