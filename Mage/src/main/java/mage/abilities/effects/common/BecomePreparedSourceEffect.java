package mage.abilities.effects.common;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.effects.OneShotEffect;
import mage.cards.Card;
import mage.cards.PrepareCard;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.util.CardUtil;

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

        // 722.3a: A permanent that is already prepared can't become
        // prepared a second time and must not create another copy.
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

        // The prepare spell template lives outside the game. Create a real
        // XMage card-copy object from that template.
        Card spellCopy = game.copyCard(
                prepareCard.getSpellCard(),
                source,
                permanent.getControllerId()
        );

        // Prepare copies are created in exile.
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

        // Associate this exceptional persistent card copy with the exact
        // battlefield object (including its zone-change counter).
        game.getState().setValue(
                PrepareCard.getPrepareCopyKey(spellCopy.getId()),
                new MageObjectReference(permanent, game)
        );

        permanent.setPrepared(true, game);
        return true;
    }
}
