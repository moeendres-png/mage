package mage.cards.t;

import mage.abilities.Ability;
import mage.abilities.common.SimpleActivatedAbility;
import mage.abilities.costs.common.TapSourceCost;
import mage.abilities.costs.mana.GenericManaCost;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.PhaseOutHeldBySourceEffect;
import mage.abilities.effects.common.counter.AddCountersSourceEffect;
import mage.abilities.triggers.BeginningOfUpkeepTriggeredAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SuperType;
import mage.constants.TimingRule;
import mage.counters.CounterType;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.target.common.TargetControlledCreaturePermanent;

import java.util.ArrayList;
import java.util.UUID;

/**
 * The Moment {2}
 * Legendary Artifact
 * At the beginning of your upkeep, put a time counter on The Moment.
 * {2}, {T}: Untap target creature you control. It phases out until The Moment leaves the battlefield.
 * {3}, {T}: Destroy each nonland permanent with mana value less than or equal to the number of time counters
 * on The Moment. Then sacrifice The Moment. Activate only as a sorcery.
 */
public final class TheMoment extends CardImpl {

    public TheMoment(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT}, "{2}");

        this.supertype.add(SuperType.LEGENDARY);

        // At the beginning of your upkeep, put a time counter on The Moment.
        this.addAbility(new BeginningOfUpkeepTriggeredAbility(new AddCountersSourceEffect(CounterType.TIME.createInstance())));

        // {2}, {T}: Untap target creature you control. It phases out until The Moment leaves the battlefield.
        Ability phaseOut = new SimpleActivatedAbility(new PhaseOutHeldBySourceEffect(false), new GenericManaCost(2));
        phaseOut.addCost(new TapSourceCost());
        phaseOut.addTarget(new TargetControlledCreaturePermanent());
        this.addAbility(phaseOut);

        // {3}, {T}: Destroy each nonland permanent with mana value less than or equal to the number of time counters
        // on The Moment. Then sacrifice The Moment. Activate only as a sorcery.
        Ability wipe = new SimpleActivatedAbility(new TheMomentEffect(), new GenericManaCost(3)).setTiming(TimingRule.SORCERY);
        wipe.addCost(new TapSourceCost());
        this.addAbility(wipe);
    }

    private TheMoment(final TheMoment card) {
        super(card);
    }

    @Override
    public TheMoment copy() {
        return new TheMoment(this);
    }
}

class TheMomentEffect extends OneShotEffect {

    TheMomentEffect() {
        super(Outcome.DestroyPermanent);
        staticText = "destroy each nonland permanent with mana value less than or equal to the number of time counters "
                + "on {this}. Then sacrifice {this}";
    }

    private TheMomentEffect(final TheMomentEffect effect) {
        super(effect);
    }

    @Override
    public TheMomentEffect copy() {
        return new TheMomentEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent moment = source.getSourcePermanentOrLKI(game);
        int counters = moment == null ? 0 : moment.getCounters(game).getCount(CounterType.TIME);
        // destroying is simultaneous: collect first
        for (Permanent permanent : new ArrayList<>(game.getBattlefield().getActivePermanents(
                StaticFilters.FILTER_PERMANENT_NON_LAND, source.getControllerId(), source, game))) {
            if (permanent.getManaValue() <= counters) {
                permanent.destroy(source, game, false);
            }
        }
        game.processAction();
        Permanent stillThere = source.getSourcePermanentIfItStillExists(game);
        if (stillThere != null) {
            stillThere.sacrifice(source, game);
        }
        return true;
    }
}
