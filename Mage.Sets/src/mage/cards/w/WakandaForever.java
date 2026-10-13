package mage.cards.w;

import mage.abilities.Ability;
import mage.abilities.effects.OneShotEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.counters.Counters;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.players.Player;
import mage.target.TargetCard;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class WakandaForever extends CardImpl {

    public WakandaForever(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.SORCERY}, "{4}{G}{G}");

        // Reveal the top six cards of your library. You may put a permanent card from among them onto the battlefield with an indestructible counter on it. You may put a permanent card from among them into your hand. Put the rest into your graveyard.
        this.getSpellAbility().addEffect(new WakandaForeverEffect());
    }

    private WakandaForever(final WakandaForever card) {
        super(card);
    }

    @Override
    public WakandaForever copy() {
        return new WakandaForever(this);
    }
}

class WakandaForeverEffect extends OneShotEffect {

    WakandaForeverEffect() {
        super(Outcome.PutCardInPlay);
        staticText = "reveal the top six cards of your library. You may put a permanent card from among them "
                + "onto the battlefield with an indestructible counter on it. You may put a permanent card "
                + "from among them into your hand. Put the rest into your graveyard";
    }

    private WakandaForeverEffect(final WakandaForeverEffect effect) {
        super(effect);
    }

    @Override
    public WakandaForeverEffect copy() {
        return new WakandaForeverEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        Cards cards = new CardsImpl(controller.getLibrary().getTopCards(game, 6));
        if (cards.isEmpty()) {
            return false;
        }
        controller.revealCards(source, cards, game);

        TargetCard target = new TargetCard(0, 1, Zone.ALL, StaticFilters.FILTER_CARD_PERMANENT);
        target.withChooseHint("to put onto the battlefield with an indestructible counter");
        controller.choose(Outcome.PutCardInPlay, cards, target, source, game);
        Card toBattlefield = game.getCard(target.getFirstTarget());
        if (toBattlefield != null) {
            game.setEnterWithCounters(toBattlefield.getId(),
                    new Counters().addCounter(CounterType.INDESTRUCTIBLE.createInstance()));
            controller.moveCards(toBattlefield, Zone.BATTLEFIELD, source, game);
            cards.remove(toBattlefield);
        }

        target = new TargetCard(0, 1, Zone.ALL, StaticFilters.FILTER_CARD_PERMANENT);
        target.withChooseHint("to put into your hand");
        controller.choose(Outcome.DrawCard, cards, target, source, game);
        Card toHand = game.getCard(target.getFirstTarget());
        if (toHand != null) {
            controller.moveCards(toHand, Zone.HAND, source, game);
            cards.remove(toHand);
        }

        cards.retainZone(Zone.LIBRARY, game);
        controller.moveCards(cards, Zone.GRAVEYARD, source, game);
        return true;
    }
}
