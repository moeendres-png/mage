package mage.cards.f;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.DelayedTriggeredAbility;
import mage.abilities.condition.common.ControlYourCommanderCondition;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.BecomesMonarchSourceEffect;
import mage.abilities.effects.common.FightTargetsEffect;
import mage.abilities.effects.common.counter.AddCountersTargetEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.counters.CounterType;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.events.ZoneChangeEvent;
import mage.game.permanent.Permanent;
import mage.target.common.TargetControlledCreaturePermanent;
import mage.target.common.TargetOpponentsCreaturePermanent;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class FightForTheThrone extends CardImpl {

    public FightForTheThrone(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.INSTANT}, "{1}{G}");

        // Put a +1/+1 counter on target creature you control. Then it fights target creature an opponent controls. When the creature an opponent controls dies this turn, if you control your commander, you become the monarch.
        this.getSpellAbility().addEffect(new AddCountersTargetEffect(CounterType.P1P1.createInstance()));
        // the "dies this turn" watch starts before the fight, so a death in the fight itself counts
        this.getSpellAbility().addEffect(new FightForTheThroneDelayedEffect());
        this.getSpellAbility().addEffect(new FightTargetsEffect()
                .setText("Then it fights target creature an opponent controls"));
        this.getSpellAbility().addTarget(new TargetControlledCreaturePermanent());
        this.getSpellAbility().addTarget(new TargetOpponentsCreaturePermanent());
    }

    private FightForTheThrone(final FightForTheThrone card) {
        super(card);
    }

    @Override
    public FightForTheThrone copy() {
        return new FightForTheThrone(this);
    }
}

class FightForTheThroneDelayedEffect extends OneShotEffect {

    FightForTheThroneDelayedEffect() {
        super(Outcome.Benefit);
        staticText = "";
    }

    private FightForTheThroneDelayedEffect(final FightForTheThroneDelayedEffect effect) {
        super(effect);
    }

    @Override
    public FightForTheThroneDelayedEffect copy() {
        return new FightForTheThroneDelayedEffect(this);
    }

    @Override
    public String getText(mage.abilities.Mode mode) {
        return "When the creature an opponent controls dies this turn, if you control your commander, "
                + "you become the monarch";
    }

    @Override
    public boolean apply(Game game, Ability source) {
        if (source.getTargets().size() < 2) {
            return false;
        }
        Permanent creature = game.getPermanent(source.getTargets().get(1).getFirstTarget());
        if (creature == null) {
            return false;
        }
        game.addDelayedTriggeredAbility(new FightForTheThroneDelayedTriggeredAbility(
                new MageObjectReference(creature, game)
        ), source);
        return true;
    }
}

class FightForTheThroneDelayedTriggeredAbility extends DelayedTriggeredAbility {

    private final MageObjectReference mor;

    FightForTheThroneDelayedTriggeredAbility(MageObjectReference mor) {
        super(new BecomesMonarchSourceEffect(), Duration.EndOfTurn, true, false);
        this.mor = mor;
        withInterveningIf(ControlYourCommanderCondition.instance);
        setTriggerPhrase("When the creature an opponent controls dies this turn, ");
    }

    private FightForTheThroneDelayedTriggeredAbility(final FightForTheThroneDelayedTriggeredAbility ability) {
        super(ability);
        this.mor = ability.mor;
    }

    @Override
    public FightForTheThroneDelayedTriggeredAbility copy() {
        return new FightForTheThroneDelayedTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.ZONE_CHANGE;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        ZoneChangeEvent zEvent = (ZoneChangeEvent) event;
        return zEvent.isDiesEvent() && mor.refersTo(zEvent.getTarget(), game);
    }
}
