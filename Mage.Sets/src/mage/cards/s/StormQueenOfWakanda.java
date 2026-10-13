package mage.cards.s;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.dynamicvalue.common.SourcePermanentPowerValue;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.DamageTargetEffect;
import mage.abilities.effects.common.continuous.BoostTargetEffect;
import mage.abilities.effects.common.continuous.GainAbilityTargetEffect;
import mage.abilities.keyword.FlyingAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.common.FilterAttackingCreature;
import mage.filter.predicate.mageobject.AnotherPredicate;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.target.TargetPermanent;
import mage.target.targetpointer.FixedTarget;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class StormQueenOfWakanda extends CardImpl {

    private static final FilterAttackingCreature filter = new FilterAttackingCreature("another target attacking creature");

    static {
        filter.add(AnotherPredicate.instance);
    }

    public StormQueenOfWakanda(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{3}{G}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.MUTANT);
        this.subtype.add(SubType.NOBLE);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(4);
        this.toughness = new MageInt(5);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // Whenever Storm attacks, until end of turn, another target attacking creature gains flying and gets +X/+0, where X is Storm's power.
        Ability ability = new AttacksTriggeredAbility(new StormQueenOfWakandaEffect());
        ability.addTarget(new TargetPermanent(filter));
        this.addAbility(ability);

        // Whenever a creature with flying attacks you, Storm deals damage equal to her power to that creature.
        this.addAbility(new StormQueenOfWakandaTriggeredAbility());
    }

    private StormQueenOfWakanda(final StormQueenOfWakanda card) {
        super(card);
    }

    @Override
    public StormQueenOfWakanda copy() {
        return new StormQueenOfWakanda(this);
    }
}

class StormQueenOfWakandaEffect extends OneShotEffect {

    StormQueenOfWakandaEffect() {
        super(Outcome.BoostCreature);
        staticText = "until end of turn, another target attacking creature gains flying and gets +X/+0, "
                + "where X is {this}'s power";
    }

    private StormQueenOfWakandaEffect(final StormQueenOfWakandaEffect effect) {
        super(effect);
    }

    @Override
    public StormQueenOfWakandaEffect copy() {
        return new StormQueenOfWakandaEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent target = game.getPermanent(getTargetPointer().getFirst(game, source));
        if (target == null) {
            return false;
        }
        // X is locked in as the ability resolves (last known power if Storm has left)
        int power = SourcePermanentPowerValue.NOT_NEGATIVE.calculate(game, source, this);
        game.addEffect(new GainAbilityTargetEffect(FlyingAbility.getInstance(), Duration.EndOfTurn)
                .setTargetPointer(new FixedTarget(target, game)), source);
        game.addEffect(new BoostTargetEffect(power, 0, Duration.EndOfTurn)
                .setTargetPointer(new FixedTarget(target, game)), source);
        return true;
    }
}

class StormQueenOfWakandaTriggeredAbility extends TriggeredAbilityImpl {

    StormQueenOfWakandaTriggeredAbility() {
        super(Zone.BATTLEFIELD, new DamageTargetEffect(SourcePermanentPowerValue.NOT_NEGATIVE)
                .setText("{this} deals damage equal to her power to that creature"));
        setTriggerPhrase("Whenever a creature with flying attacks you, ");
    }

    private StormQueenOfWakandaTriggeredAbility(final StormQueenOfWakandaTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public StormQueenOfWakandaTriggeredAbility copy() {
        return new StormQueenOfWakandaTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.ATTACKER_DECLARED;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!isControlledBy(event.getTargetId())) {
            return false;
        }
        Permanent attacker = game.getPermanent(event.getSourceId());
        if (attacker == null || !attacker.hasAbility(FlyingAbility.getInstance(), game)) {
            return false;
        }
        getEffects().setTargetPointer(new FixedTarget(attacker, game));
        return true;
    }
}
