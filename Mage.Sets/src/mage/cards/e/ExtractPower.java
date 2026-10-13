package mage.cards.e;

import mage.abilities.Ability;
import mage.abilities.effects.ContinuousEffect;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.asthought.MayLookAtTargetCardEffect;
import mage.abilities.effects.common.asthought.PlayFromNotOwnHandZoneTargetEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.TargetController;
import mage.constants.Zone;
import mage.game.Game;
import mage.players.Player;
import mage.target.targetpointer.FixedTarget;
import mage.util.CardUtil;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class ExtractPower extends CardImpl {

    public ExtractPower(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.SORCERY}, "{5}{U}");

        // Look at the top card of each player's library, then exile those cards face down. You may play them without paying their mana costs for as long as they remain exiled.
        this.getSpellAbility().addEffect(new ExtractPowerEffect());
    }

    private ExtractPower(final ExtractPower card) {
        super(card);
    }

    @Override
    public ExtractPower copy() {
        return new ExtractPower(this);
    }
}

class ExtractPowerEffect extends OneShotEffect {

    ExtractPowerEffect() {
        super(Outcome.PlayForFree);
        staticText = "look at the top card of each player's library, then exile those cards face down. "
                + "You may play them without paying their mana costs for as long as they remain exiled";
    }

    private ExtractPowerEffect(final ExtractPowerEffect effect) {
        super(effect);
    }

    @Override
    public ExtractPowerEffect copy() {
        return new ExtractPowerEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        Cards cards = new CardsImpl();
        for (UUID playerId : game.getState().getPlayersInRange(controller.getId(), game)) {
            Player player = game.getPlayer(playerId);
            if (player != null) {
                Card card = player.getLibrary().getFromTop(game);
                if (card != null) {
                    cards.add(card);
                }
            }
        }
        if (cards.isEmpty()) {
            return true;
        }
        controller.lookAtCards(source, null, cards, game);
        UUID exileZoneId = CardUtil.getExileZoneId(game, source);
        controller.moveCardsToExile(cards.getCards(game), source, game, false, exileZoneId, CardUtil.getSourceName(game, source));
        for (Card card : cards.getCards(game)) {
            if (game.getState().getZone(card.getId()) != Zone.EXILED) {
                continue;
            }
            card.setFaceDown(true, game);
            ContinuousEffect effect = new PlayFromNotOwnHandZoneTargetEffect(Zone.EXILED, TargetController.YOU, Duration.Custom, true);
            effect.setTargetPointer(new FixedTarget(card.getId(), game.getState().getZoneChangeCounter(card.getId())));
            game.addEffect(effect, source);
            ContinuousEffect look = new MayLookAtTargetCardEffect(controller.getId());
            look.setTargetPointer(new FixedTarget(card.getId(), game.getState().getZoneChangeCounter(card.getId())));
            game.addEffect(look, source);
        }
        return true;
    }
}
