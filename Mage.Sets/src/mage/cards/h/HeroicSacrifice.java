package mage.cards.h;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.DelayedTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.ReplacementEffectImpl;
import mage.abilities.effects.common.DrawCardSourceControllerEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.counters.Counter;
import mage.counters.Counters;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.game.events.DamageEvent;
import mage.game.events.GameEvent;
import mage.game.events.ZoneChangeEvent;
import mage.game.permanent.Permanent;
import mage.target.TargetPermanent;
import mage.target.common.TargetControlledCreaturePermanent;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class HeroicSacrifice extends CardImpl {

    public HeroicSacrifice(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.INSTANT}, "{1}{W}");

        // Choose target creature you control. Until end of turn, all damage that would be dealt to you and creatures you control is dealt to the chosen creature instead (if it's still on the battlefield). When that creature dies this turn, put its counters on up to one target creature you control and draw a card.
        this.getSpellAbility().addEffect(new HeroicSacrificeEffect());
        this.getSpellAbility().addTarget(new TargetControlledCreaturePermanent());
    }

    private HeroicSacrifice(final HeroicSacrifice card) {
        super(card);
    }

    @Override
    public HeroicSacrifice copy() {
        return new HeroicSacrifice(this);
    }
}

class HeroicSacrificeEffect extends OneShotEffect {

    HeroicSacrificeEffect() {
        super(Outcome.RedirectDamage);
        staticText = "Choose target creature you control. Until end of turn, all damage that would be dealt to you "
                + "and creatures you control is dealt to the chosen creature instead (if it's still on the battlefield). "
                + "When that creature dies this turn, put its counters on up to one target creature you control and draw a card";
    }

    private HeroicSacrificeEffect(final HeroicSacrificeEffect effect) {
        super(effect);
    }

    @Override
    public HeroicSacrificeEffect copy() {
        return new HeroicSacrificeEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent chosen = game.getPermanent(getTargetPointer().getFirst(game, source));
        if (chosen == null) {
            return false;
        }
        MageObjectReference mor = new MageObjectReference(chosen, game);
        game.addEffect(new HeroicSacrificeReplacementEffect(mor), source);
        game.addDelayedTriggeredAbility(new HeroicSacrificeDelayedTriggeredAbility(mor), source);
        return true;
    }
}

class HeroicSacrificeReplacementEffect extends ReplacementEffectImpl {

    private final MageObjectReference chosen;

    HeroicSacrificeReplacementEffect(MageObjectReference chosen) {
        super(Duration.EndOfTurn, Outcome.RedirectDamage);
        this.chosen = chosen;
    }

    private HeroicSacrificeReplacementEffect(final HeroicSacrificeReplacementEffect effect) {
        super(effect);
        this.chosen = effect.chosen;
    }

    @Override
    public HeroicSacrificeReplacementEffect copy() {
        return new HeroicSacrificeReplacementEffect(this);
    }

    @Override
    public boolean checksEventType(GameEvent event, Game game) {
        switch (event.getType()) {
            case DAMAGE_PERMANENT:
            case DAMAGE_PLAYER:
                return true;
            default:
                return false;
        }
    }

    @Override
    public boolean applies(GameEvent event, Ability source, Game game) {
        Permanent chosenPermanent = chosen.getPermanent(game);
        if (chosenPermanent == null) {
            return false;
        }
        if (event.getType() == GameEvent.EventType.DAMAGE_PLAYER) {
            return event.getTargetId().equals(source.getControllerId());
        }
        if (event.getTargetId().equals(chosenPermanent.getId())) {
            return false;
        }
        Permanent damaged = game.getPermanent(event.getTargetId());
        return damaged != null && damaged.isCreature(game) && damaged.isControlledBy(source.getControllerId());
    }

    @Override
    public boolean replaceEvent(GameEvent event, Ability source, Game game) {
        Permanent chosenPermanent = chosen.getPermanent(game);
        if (chosenPermanent == null) {
            return false;
        }
        DamageEvent damageEvent = (DamageEvent) event;
        chosenPermanent.damage(damageEvent.getAmount(), damageEvent.getSourceId(), source, game,
                damageEvent.isCombatDamage(), damageEvent.isPreventable(), event.getAppliedEffects());
        return true;
    }
}

class HeroicSacrificeDelayedTriggeredAbility extends DelayedTriggeredAbility {

    private final MageObjectReference chosen;

    HeroicSacrificeDelayedTriggeredAbility(MageObjectReference chosen) {
        super(new HeroicSacrificeCountersEffect(), Duration.EndOfTurn, true, false);
        this.addEffect(new DrawCardSourceControllerEffect(1).concatBy("and"));
        this.addTarget(new TargetPermanent(0, 1, StaticFilters.FILTER_CONTROLLED_CREATURE));
        this.chosen = chosen;
        setTriggerPhrase("When that creature dies this turn, ");
    }

    private HeroicSacrificeDelayedTriggeredAbility(final HeroicSacrificeDelayedTriggeredAbility ability) {
        super(ability);
        this.chosen = ability.chosen;
    }

    @Override
    public HeroicSacrificeDelayedTriggeredAbility copy() {
        return new HeroicSacrificeDelayedTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.ZONE_CHANGE;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        ZoneChangeEvent zEvent = (ZoneChangeEvent) event;
        if (!zEvent.isDiesEvent() || zEvent.getTarget() == null
                || !chosen.refersTo(zEvent.getTarget(), game)) {
            return false;
        }
        getEffects().setValue("diedCounters", zEvent.getTarget().getCounters(game).copy());
        return true;
    }
}

class HeroicSacrificeCountersEffect extends OneShotEffect {

    HeroicSacrificeCountersEffect() {
        super(Outcome.BoostCreature);
        staticText = "put its counters on up to one target creature you control";
    }

    private HeroicSacrificeCountersEffect(final HeroicSacrificeCountersEffect effect) {
        super(effect);
    }

    @Override
    public HeroicSacrificeCountersEffect copy() {
        return new HeroicSacrificeCountersEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent target = game.getPermanent(getTargetPointer().getFirst(game, source));
        Counters counters = (Counters) getValue("diedCounters");
        if (target == null || counters == null) {
            return false;
        }
        for (Counter counter : counters.values()) {
            if (counter.getCount() > 0) {
                target.addCounters(counter.copy(), source, game);
            }
        }
        return true;
    }
}
