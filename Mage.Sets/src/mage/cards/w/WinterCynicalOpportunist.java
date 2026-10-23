package mage.cards.w;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.MillCardsControllerEffect;
import mage.abilities.keyword.DeathtouchAbility;
import mage.abilities.triggers.BeginningOfEndStepTriggeredAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.AbilityWord;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.TargetController;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.counters.Counters;
import mage.filter.FilterCard;
import mage.filter.predicate.mageobject.PermanentPredicate;
import mage.game.Game;
import mage.players.Player;
import mage.target.TargetCard;
import mage.target.common.TargetCardInYourGraveyard;

import java.util.EnumSet;
import java.util.Set;
import java.util.UUID;

/**
 * @author Claude
 */
public final class WinterCynicalOpportunist extends CardImpl {

    public WinterCynicalOpportunist(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{B}{G}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.WARLOCK);
        this.power = new MageInt(2);
        this.toughness = new MageInt(5);

        // Deathtouch
        this.addAbility(DeathtouchAbility.getInstance());

        // Whenever Winter attacks, mill three cards.
        this.addAbility(new AttacksTriggeredAbility(new MillCardsControllerEffect(3)));

        // Delirium -- At the beginning of your end step, you may exile any number of cards from your graveyard
        // with four or more card types among them. If you do, put a permanent card from among them onto the
        // battlefield with a finality counter on it.
        Ability ability = new BeginningOfEndStepTriggeredAbility(
                TargetController.YOU, new WinterCynicalOpportunistEffect(), false
        );
        ability.setAbilityWord(AbilityWord.DELIRIUM);
        this.addAbility(ability);
    }

    private WinterCynicalOpportunist(final WinterCynicalOpportunist card) {
        super(card);
    }

    @Override
    public WinterCynicalOpportunist copy() {
        return new WinterCynicalOpportunist(this);
    }
}

class WinterCynicalOpportunistEffect extends OneShotEffect {

    private static final FilterCard exileFilter
            = new FilterCard("any number of cards from your graveyard with four or more card types among them");
    private static final FilterCard permanentFilter = new FilterCard("a permanent card from among the exiled cards");

    static {
        permanentFilter.add(PermanentPredicate.instance);
    }

    WinterCynicalOpportunistEffect() {
        super(Outcome.PutCardInPlay);
        staticText = "you may exile any number of cards from your graveyard with four or more card types among them. "
                + "If you do, put a permanent card from among them onto the battlefield with a finality counter on it";
    }

    private WinterCynicalOpportunistEffect(final WinterCynicalOpportunistEffect effect) {
        super(effect);
    }

    @Override
    public WinterCynicalOpportunistEffect copy() {
        return new WinterCynicalOpportunistEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null || controller.getGraveyard().isEmpty()) {
            return false;
        }
        if (!controller.chooseUse(Outcome.PutCardInPlay,
                "Exile cards from your graveyard with four or more card types among them?", source, game)) {
            return false;
        }
        TargetCard target = new TargetCardInYourGraveyard(0, Integer.MAX_VALUE, exileFilter);
        target.withNotTarget(true);
        controller.chooseTarget(Outcome.PutCardInPlay, controller.getGraveyard(), target, source, game);
        Cards chosen = new CardsImpl(target.getTargets());
        if (typesAmong(chosen, game) < 4) {
            // delirium needs four card types among the exiled cards: nothing is exiled
            return false;
        }
        controller.moveCards(chosen, Zone.EXILED, source, game);
        game.processAction();
        Cards permanents = new CardsImpl();
        for (Card card : chosen.getCards(game)) {
            if (game.getState().getZone(card.getId()) == Zone.EXILED && card.isPermanent(game)) {
                permanents.add(card);
            }
        }
        if (permanents.isEmpty()) {
            return true;
        }
        TargetCard permanentTarget = new TargetCard(Zone.EXILED, permanentFilter);
        permanentTarget.withNotTarget(true);
        controller.chooseTarget(Outcome.PutCardInPlay, permanents, permanentTarget, source, game);
        Card card = game.getCard(permanentTarget.getFirstTarget());
        if (card != null) {
            Counters counters = new Counters();
            counters.addCounter(CounterType.FINALITY.createInstance());
            game.setEnterWithCounters(card.getId(), counters);
            controller.moveCards(card, Zone.BATTLEFIELD, source, game);
        }
        return true;
    }

    private static int typesAmong(Cards cards, Game game) {
        Set<CardType> types = EnumSet.noneOf(CardType.class);
        for (Card card : cards.getCards(game)) {
            types.addAll(card.getCardType(game));
        }
        return types.size();
    }
}
