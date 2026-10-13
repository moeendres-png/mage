package mage.cards.l;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.delayed.ReflexiveTriggeredAbility;
import mage.abilities.condition.common.CastNoncreatureSpellThisTurnCondition;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.combat.CantBeBlockedSourceEffect;
import mage.abilities.effects.common.combat.CantBeBlockedTargetEffect;
import mage.abilities.keyword.VigilanceAbility;
import mage.abilities.triggers.BeginningOfCombatTriggeredAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.counters.CounterType;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.target.TargetPermanent;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class LockjawSlobberingTeleporter extends CardImpl {

    public LockjawSlobberingTeleporter(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{1}{U}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.INHUMAN);
        this.subtype.add(SubType.DOG);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(1);
        this.toughness = new MageInt(1);

        // Vigilance
        this.addAbility(VigilanceAbility.getInstance());

        // At the beginning of combat on your turn, if you've cast a noncreature spell this turn, put a +1/+1 counter on Lockjaw. When you do, Lockjaw and up to one other target creature you control can't be blocked this turn.
        this.addAbility(new BeginningOfCombatTriggeredAbility(new LockjawSlobberingTeleporterEffect())
                .withInterveningIf(CastNoncreatureSpellThisTurnCondition.instance)
                .addHint(CastNoncreatureSpellThisTurnCondition.getHint()));
    }

    private LockjawSlobberingTeleporter(final LockjawSlobberingTeleporter card) {
        super(card);
    }

    @Override
    public LockjawSlobberingTeleporter copy() {
        return new LockjawSlobberingTeleporter(this);
    }
}

class LockjawSlobberingTeleporterEffect extends OneShotEffect {

    LockjawSlobberingTeleporterEffect() {
        super(Outcome.BoostCreature);
        staticText = "put a +1/+1 counter on {this}. When you do, {this} and up to one other "
                + "target creature you control can't be blocked this turn";
    }

    private LockjawSlobberingTeleporterEffect(final LockjawSlobberingTeleporterEffect effect) {
        super(effect);
    }

    @Override
    public LockjawSlobberingTeleporterEffect copy() {
        return new LockjawSlobberingTeleporterEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent permanent = source.getSourcePermanentIfItStillExists(game);
        if (permanent == null || !permanent.addCounters(CounterType.P1P1.createInstance(), source, game)) {
            return false;
        }
        ReflexiveTriggeredAbility ability = new ReflexiveTriggeredAbility(
                new CantBeBlockedSourceEffect(Duration.EndOfTurn), false,
                "{this} and up to one other target creature you control can't be blocked this turn"
        );
        ability.addEffect(new CantBeBlockedTargetEffect(Duration.EndOfTurn));
        ability.addTarget(new TargetPermanent(
                0, 1, StaticFilters.FILTER_ANOTHER_CREATURE_YOU_CONTROL
        ));
        game.fireReflexiveTriggeredAbility(ability, source);
        return true;
    }
}
