package mage.cards.h;

import mage.abilities.Ability;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.condition.Condition;
import mage.abilities.condition.common.PermanentsOnTheBattlefieldCondition;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.cost.SpellCostReductionSourceEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.counters.Counters;
import mage.filter.StaticFilters;
import mage.filter.common.FilterCreatureAttackingYou;
import mage.game.Game;
import mage.players.Player;
import mage.target.common.TargetCardInYourGraveyard;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class HeroicReturn extends CardImpl {

    private static final Condition condition = new PermanentsOnTheBattlefieldCondition(
            new FilterCreatureAttackingYou("a creature is attacking you"), false
    );

    public HeroicReturn(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.INSTANT}, "{5}{W}");

        // This spell costs {2} less to cast if a creature is attacking you.
        this.addAbility(new SimpleStaticAbility(
                Zone.ALL, new SpellCostReductionSourceEffect(2, condition)
        ).setRuleAtTheTop(true));

        // Return target creature card from your graveyard to the battlefield. If a Hero enters this way, it enters with two additional +1/+1 counters on it.
        this.getSpellAbility().addEffect(new HeroicReturnEffect());
        this.getSpellAbility().addTarget(new TargetCardInYourGraveyard(StaticFilters.FILTER_CARD_CREATURE_YOUR_GRAVEYARD));
    }

    private HeroicReturn(final HeroicReturn card) {
        super(card);
    }

    @Override
    public HeroicReturn copy() {
        return new HeroicReturn(this);
    }
}

class HeroicReturnEffect extends OneShotEffect {

    HeroicReturnEffect() {
        super(Outcome.PutCreatureInPlay);
        staticText = "return target creature card from your graveyard to the battlefield. "
                + "If a Hero enters this way, it enters with two additional +1/+1 counters on it";
    }

    private HeroicReturnEffect(final HeroicReturnEffect effect) {
        super(effect);
    }

    @Override
    public HeroicReturnEffect copy() {
        return new HeroicReturnEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Card card = game.getCard(getTargetPointer().getFirst(game, source));
        if (controller == null || card == null) {
            return false;
        }
        // A creature card's subtypes are the same in the graveyard and as it enters (no copy/face effects apply here).
        if (card.hasSubtype(SubType.HERO, game)) {
            game.setEnterWithCounters(card.getId(), new Counters().addCounter(CounterType.P1P1.createInstance(2)));
        }
        return controller.moveCards(card, Zone.BATTLEFIELD, source, game);
    }
}
