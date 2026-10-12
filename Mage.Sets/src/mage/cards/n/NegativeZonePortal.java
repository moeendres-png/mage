package mage.cards.n;

import mage.abilities.Ability;
import mage.abilities.common.SimpleActivatedAbility;
import mage.abilities.condition.Condition;
import mage.abilities.costs.common.TapSourceCost;
import mage.abilities.costs.mana.GenericManaCost;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.triggers.BeginningOfUpkeepTriggeredAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.filter.StaticFilters;
import mage.game.ExileZone;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.common.TargetCardInOpponentsGraveyard;
import mage.util.CardUtil;
import mage.util.RandomUtil;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * @author commander-lab
 */
public final class NegativeZonePortal extends CardImpl {

    public NegativeZonePortal(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT}, "{2}");

        // {2}, {T}: Exile target card from an opponent's graveyard. If it's a creature card, draw a card.
        Ability ability = new SimpleActivatedAbility(new NegativeZonePortalExileEffect(), new GenericManaCost(2));
        ability.addCost(new TapSourceCost());
        ability.addTarget(new TargetCardInOpponentsGraveyard(StaticFilters.FILTER_CARD));
        this.addAbility(ability);

        // At the beginning of your upkeep, if there are four or more creature cards exiled with this artifact, flip a coin. If you lose the flip, sacrifice this artifact and return a card exiled with it at random to its owner's hand.
        this.addAbility(new BeginningOfUpkeepTriggeredAbility(new NegativeZonePortalFlipEffect())
                .withInterveningIf(NegativeZonePortalCondition.instance));
    }

    private NegativeZonePortal(final NegativeZonePortal card) {
        super(card);
    }

    @Override
    public NegativeZonePortal copy() {
        return new NegativeZonePortal(this);
    }
}

enum NegativeZonePortalCondition implements Condition {
    instance;

    @Override
    public boolean apply(Game game, Ability source) {
        ExileZone exile = game.getExile().getExileZone(NegativeZonePortalCondition.exileZoneId(game, source));
        return exile != null && exile.count(StaticFilters.FILTER_CARD_CREATURE, game) >= 4;
    }

    /**
     * The zone of cards exiled with this permanent. Uses the permanent's current zone change
     * counter: the intervening-if check runs before the trigger is on the stack.
     */
    static UUID exileZoneId(Game game, Ability source) {
        return CardUtil.getExileZoneId(game, source.getSourceId(),
                game.getState().getZoneChangeCounter(source.getSourceId()));
    }

    @Override
    public String toString() {
        return "there are four or more creature cards exiled with {this}";
    }
}

class NegativeZonePortalExileEffect extends OneShotEffect {

    NegativeZonePortalExileEffect() {
        super(Outcome.Exile);
        staticText = "exile target card from an opponent's graveyard. If it's a creature card, draw a card";
    }

    private NegativeZonePortalExileEffect(final NegativeZonePortalExileEffect effect) {
        super(effect);
    }

    @Override
    public NegativeZonePortalExileEffect copy() {
        return new NegativeZonePortalExileEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Card card = game.getCard(getTargetPointer().getFirst(game, source));
        if (controller == null || card == null) {
            return false;
        }
        boolean creature = card.isCreature(game);
        controller.moveCardsToExile(card, source, game, true,
                CardUtil.getExileZoneId(game, source), CardUtil.getSourceName(game, source));
        if (creature && game.getState().getZone(card.getId()) == Zone.EXILED) {
            controller.drawCards(1, source, game);
        }
        return true;
    }
}

class NegativeZonePortalFlipEffect extends OneShotEffect {

    NegativeZonePortalFlipEffect() {
        super(Outcome.Neutral);
        staticText = "flip a coin. If you lose the flip, sacrifice this artifact and return a card exiled with it at random to its owner's hand";
    }

    private NegativeZonePortalFlipEffect(final NegativeZonePortalFlipEffect effect) {
        super(effect);
    }

    @Override
    public NegativeZonePortalFlipEffect copy() {
        return new NegativeZonePortalFlipEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        if (controller.flipCoin(source, game, true)) {
            return true;
        }
        ExileZone exile = game.getExile().getExileZone(NegativeZonePortalCondition.exileZoneId(game, source));
        Permanent permanent = source.getSourcePermanentIfItStillExists(game);
        if (permanent != null) {
            permanent.sacrifice(source, game);
        }
        if (exile == null || exile.isEmpty()) {
            return true;
        }
        List<Card> cards = new ArrayList<>(exile.getCards(game));
        Card card = RandomUtil.randomFromCollection(cards, game.getRulesRandom());
        if (card != null) {
            Player owner = game.getPlayer(card.getOwnerId());
            if (owner != null) {
                owner.moveCards(card, Zone.HAND, source, game);
            }
        }
        return true;
    }
}
