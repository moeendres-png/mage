package mage.cards.t;

import mage.MageInt;
import mage.abilities.BatchTriggeredAbility;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.common.EntersBattlefieldTriggeredAbility;
import mage.abilities.condition.common.MonarchIsSourceControllerCondition;
import mage.abilities.effects.common.BecomesMonarchSourceEffect;
import mage.abilities.effects.common.TapTargetEffect;
import mage.abilities.effects.common.counter.AddCountersTargetEffect;
import mage.abilities.hint.common.MonarchHint;
import mage.abilities.keyword.DoubleStrikeAbility;
import mage.abilities.keyword.FlyingAbility;
import mage.abilities.keyword.HasteAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.Game;
import mage.game.events.DamagedBatchForOnePlayerEvent;
import mage.game.events.DamagedEvent;
import mage.game.events.DamagedPlayerEvent;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.target.targetpointer.FixedTargets;

import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * @author Claude
 */
public final class TamiyoUpriserCrowned extends CardImpl {

    public TamiyoUpriserCrowned(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{4}{R}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.MOONFOLK, SubType.WARRIOR);
        this.power = new MageInt(3);
        this.toughness = new MageInt(5);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // Double strike
        this.addAbility(DoubleStrikeAbility.getInstance());

        // Haste
        this.addAbility(HasteAbility.getInstance());

        // When Tamiyo enters, you become the monarch.
        this.addAbility(new EntersBattlefieldTriggeredAbility(new BecomesMonarchSourceEffect()).addHint(MonarchHint.instance));

        // Whenever one or more creatures deal combat damage to you while you're the monarch,
        // tap those creatures and put a stun counter on each of them.
        this.addAbility(new TamiyoUpriserCrownedTriggeredAbility());
    }

    private TamiyoUpriserCrowned(final TamiyoUpriserCrowned card) {
        super(card);
    }

    @Override
    public TamiyoUpriserCrowned copy() {
        return new TamiyoUpriserCrowned(this);
    }
}

class TamiyoUpriserCrownedTriggeredAbility extends TriggeredAbilityImpl implements BatchTriggeredAbility<DamagedPlayerEvent> {

    TamiyoUpriserCrownedTriggeredAbility() {
        super(Zone.BATTLEFIELD, new TapTargetEffect().setText("tap those creatures"));
        this.addEffect(new AddCountersTargetEffect(CounterType.STUN.createInstance())
                .setText("and put a stun counter on each of them"));
        setTriggerPhrase("Whenever one or more creatures deal combat damage to you while you're the monarch, ");
    }

    private TamiyoUpriserCrownedTriggeredAbility(final TamiyoUpriserCrownedTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public TamiyoUpriserCrownedTriggeredAbility copy() {
        return new TamiyoUpriserCrownedTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DAMAGED_BATCH_FOR_ONE_PLAYER;
    }

    @Override
    public boolean checkEvent(DamagedPlayerEvent event, Game game) {
        return event.isCombatDamage() && event.getAmount() > 0;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!isControlledBy(event.getTargetId())
                || !MonarchIsSourceControllerCondition.instance.apply(game, this)) {
            return false;
        }
        List<Permanent> creatures = getFilteredEvents((DamagedBatchForOnePlayerEvent) event, game)
                .stream()
                .map(DamagedEvent::getSourceId)
                .distinct()
                .map(game::getPermanent)
                .filter(permanent -> permanent != null && permanent.isCreature(game))
                .collect(Collectors.toList());
        if (creatures.isEmpty()) {
            return false;
        }
        this.getEffects().setTargetPointer(new FixedTargets(creatures, game));
        return true;
    }
}
