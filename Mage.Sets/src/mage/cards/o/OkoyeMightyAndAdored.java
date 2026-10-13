package mage.cards.o;

import mage.abilities.hint.common.MonarchHint;
import mage.MageInt;
import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.DelayedTriggeredAbility;
import mage.abilities.common.EntersBattlefieldTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.BecomesMonarchSourceEffect;
import mage.abilities.effects.common.continuous.GainAbilityTargetEffect;
import mage.abilities.keyword.DoubleStrikeAbility;
import mage.abilities.keyword.TrampleAbility;
import mage.abilities.triggers.BeginningOfCombatTriggeredAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.counters.CounterType;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.target.common.TargetCreaturePermanent;
import mage.target.targetpointer.FixedTarget;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class OkoyeMightyAndAdored extends CardImpl {

    public OkoyeMightyAndAdored(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{G}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.WARRIOR);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(3);
        this.toughness = new MageInt(3);

        // When Okoye enters, you become the monarch.
        this.addAbility(new EntersBattlefieldTriggeredAbility(new BecomesMonarchSourceEffect()).addHint(MonarchHint.instance));

        // At the beginning of combat on your turn, put a +1/+1 counter on target creature. Whenever that creature attacks the monarch this turn, it gains double strike and trample until end of turn.
        Ability ability = new BeginningOfCombatTriggeredAbility(new OkoyeMightyAndAdoredEffect());
        ability.addTarget(new TargetCreaturePermanent());
        this.addAbility(ability);
    }

    private OkoyeMightyAndAdored(final OkoyeMightyAndAdored card) {
        super(card);
    }

    @Override
    public OkoyeMightyAndAdored copy() {
        return new OkoyeMightyAndAdored(this);
    }
}

class OkoyeMightyAndAdoredEffect extends OneShotEffect {

    OkoyeMightyAndAdoredEffect() {
        super(Outcome.BoostCreature);
        staticText = "put a +1/+1 counter on target creature. Whenever that creature attacks the monarch "
                + "this turn, it gains double strike and trample until end of turn";
    }

    private OkoyeMightyAndAdoredEffect(final OkoyeMightyAndAdoredEffect effect) {
        super(effect);
    }

    @Override
    public OkoyeMightyAndAdoredEffect copy() {
        return new OkoyeMightyAndAdoredEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent creature = game.getPermanent(getTargetPointer().getFirst(game, source));
        if (creature == null) {
            return false;
        }
        creature.addCounters(CounterType.P1P1.createInstance(), source.getControllerId(), source, game);
        game.addDelayedTriggeredAbility(new OkoyeMightyAndAdoredDelayedTriggeredAbility(
                new MageObjectReference(creature, game)
        ), source);
        return true;
    }
}

class OkoyeMightyAndAdoredDelayedTriggeredAbility extends DelayedTriggeredAbility {

    private final MageObjectReference mor;

    OkoyeMightyAndAdoredDelayedTriggeredAbility(MageObjectReference mor) {
        super(new GainAbilityTargetEffect(DoubleStrikeAbility.getInstance(), Duration.EndOfTurn)
                .setText("it gains double strike"), Duration.EndOfTurn, false, false);
        addEffect(new GainAbilityTargetEffect(TrampleAbility.getInstance(), Duration.EndOfTurn)
                .setText("and trample until end of turn"));
        this.mor = mor;
        setTriggerPhrase("Whenever that creature attacks the monarch this turn, ");
    }

    private OkoyeMightyAndAdoredDelayedTriggeredAbility(final OkoyeMightyAndAdoredDelayedTriggeredAbility ability) {
        super(ability);
        this.mor = ability.mor;
    }

    @Override
    public OkoyeMightyAndAdoredDelayedTriggeredAbility copy() {
        return new OkoyeMightyAndAdoredDelayedTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.ATTACKER_DECLARED;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!mor.refersTo(event.getSourceId(), game) || !event.getTargetId().equals(game.getMonarchId())) {
            return false;
        }
        getEffects().setTargetPointer(new FixedTarget(event.getSourceId(), game));
        return true;
    }
}
