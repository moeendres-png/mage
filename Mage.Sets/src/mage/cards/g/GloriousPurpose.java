package mage.cards.g;

import mage.abilities.Ability;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.common.ConnivesCreatureYouControlTriggeredAbility;
import mage.abilities.costs.common.SacrificeSourceCost;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.DoIfCostPaid;
import mage.abilities.effects.common.counter.AddCountersSourceEffect;
import mage.abilities.effects.common.counter.AddCountersTargetEffect;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.util.CardUtil;

import java.util.Optional;
import java.util.UUID;

/**
 * @author commander-lab
 */
public final class GloriousPurpose extends CardImpl {

    public GloriousPurpose(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ENCHANTMENT}, "{1}{U}");

        this.subtype.add(SubType.PLAN);

        // Whenever a creature you control connives, put a +1/+1 counter on that creature and a plan counter on this enchantment.
        Ability ability = new ConnivesCreatureYouControlTriggeredAbility(
                new AddCountersTargetEffect(CounterType.P1P1.createInstance()).setText("put a +1/+1 counter on that creature"),
                false, true
        );
        ability.addEffect(new AddCountersSourceEffect(CounterType.PLAN.createInstance()).concatBy("and"));
        this.addAbility(ability);

        // When the sixth plan counter is put on this enchantment, sacrifice it. If you do, exile the top four cards of your library. You may cast any number of spells from among them without paying their mana costs. Put the rest into your hand.
        this.addAbility(new GloriousPurposeTriggeredAbility());
    }

    private GloriousPurpose(final GloriousPurpose card) {
        super(card);
    }

    @Override
    public GloriousPurpose copy() {
        return new GloriousPurpose(this);
    }
}

class GloriousPurposeTriggeredAbility extends TriggeredAbilityImpl {

    private static final int THRESHOLD = 6;

    GloriousPurposeTriggeredAbility() {
        super(Zone.ALL, new DoIfCostPaid(
                new GloriousPurposeEffect(), null,
                new SacrificeSourceCost().setText("sacrifice it"), null, false
        ), false);
        setTriggerPhrase("When the sixth plan counter is put on {this}, ");
    }

    private GloriousPurposeTriggeredAbility(final GloriousPurposeTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public GloriousPurposeTriggeredAbility copy() {
        return new GloriousPurposeTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.COUNTER_ADDED;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!event.getTargetId().equals(getSourceId()) || !CounterType.PLAN.getName().equals(event.getData())) {
            return false;
        }
        int amountAdded = event.getAmount();
        Permanent sourcePermanent = Optional
                .ofNullable(game.getPermanent(getSourceId()))
                .orElse(game.getPermanentEntering(getSourceId()));
        int planCounters = sourcePermanent != null
                ? sourcePermanent.getCounters(game).getCount(CounterType.PLAN)
                : amountAdded;
        return planCounters - amountAdded < THRESHOLD && THRESHOLD <= planCounters;
    }
}

class GloriousPurposeEffect extends OneShotEffect {

    GloriousPurposeEffect() {
        super(Outcome.PlayForFree);
        staticText = "exile the top four cards of your library. You may cast any number of spells "
                + "from among them without paying their mana costs. Put the rest into your hand";
    }

    private GloriousPurposeEffect(final GloriousPurposeEffect effect) {
        super(effect);
    }

    @Override
    public GloriousPurposeEffect copy() {
        return new GloriousPurposeEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player player = game.getPlayer(source.getControllerId());
        if (player == null) {
            return false;
        }
        Cards cards = new CardsImpl(player.getLibrary().getTopCards(game, 4));
        if (cards.isEmpty()) {
            return false;
        }
        player.moveCards(cards, Zone.EXILED, source, game);
        game.processAction();
        cards.retainZone(Zone.EXILED, game);
        CardUtil.castMultipleWithAttributeForFree(player, source, game, cards, StaticFilters.FILTER_CARD);
        cards.retainZone(Zone.EXILED, game);
        player.moveCards(cards, Zone.HAND, source, game);
        return true;
    }
}
