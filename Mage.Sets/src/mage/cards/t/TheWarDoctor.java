package mage.cards.t;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.BatchTriggeredAbility;
import mage.abilities.TriggeredAbility;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.dynamicvalue.common.CountersSourceCount;
import mage.abilities.effects.common.DamageTargetEffect;
import mage.abilities.effects.common.ExileTargetIfDiesEffect;
import mage.abilities.effects.common.counter.AddCountersSourceEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.events.PhasedOutBatchEvent;
import mage.game.events.ZoneChangeBatchEvent;
import mage.game.events.ZoneChangeEvent;
import mage.target.common.TargetAnyTarget;

import java.util.UUID;

/**
 * The War Doctor {2}{R}{W}
 * Legendary Creature -- Time Lord Doctor 3/5
 * Whenever one or more other permanents phase out and whenever one or more other cards are put into exile
 * from anywhere, put a time counter on The War Doctor.
 * Whenever The War Doctor attacks, it deals damage equal to the number of time counters on it to any target.
 * If a creature dealt damage this way would die this turn, exile it instead.
 */
public final class TheWarDoctor extends CardImpl {

    public TheWarDoctor(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{R}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.TIME_LORD);
        this.subtype.add(SubType.DOCTOR);
        this.power = new MageInt(3);
        this.toughness = new MageInt(5);

        // Whenever one or more other permanents phase out and whenever one or more other cards are put into exile
        // from anywhere, put a time counter on The War Doctor.
        this.addAbility(new TheWarDoctorPhaseOutTriggeredAbility());
        this.addAbility(new TheWarDoctorExileTriggeredAbility());

        // Whenever The War Doctor attacks, it deals damage equal to the number of time counters on it to any target.
        // If a creature dealt damage this way would die this turn, exile it instead.
        TriggeredAbility ability = new AttacksTriggeredAbility(new DamageTargetEffect(
                new CountersSourceCount(CounterType.TIME), "it"
        ).setText("it deals damage equal to the number of time counters on it to any target"));
        ability.addEffect(new ExileTargetIfDiesEffect("creature dealt damage this way"));
        ability.addTarget(new TargetAnyTarget());
        // "would die" in the text makes Mage.Verify ask for the flag, an attack trigger is not hurt by it
        ability.setLeavesTheBattlefieldTrigger(true);
        this.addAbility(ability);
    }

    private TheWarDoctor(final TheWarDoctor card) {
        super(card);
    }

    @Override
    public TheWarDoctor copy() {
        return new TheWarDoctor(this);
    }
}

class TheWarDoctorPhaseOutTriggeredAbility extends TriggeredAbilityImpl implements BatchTriggeredAbility<GameEvent> {

    TheWarDoctorPhaseOutTriggeredAbility() {
        super(Zone.BATTLEFIELD, new AddCountersSourceEffect(CounterType.TIME.createInstance()), false);
        setTriggerPhrase("Whenever one or more other permanents phase out, ");
    }

    private TheWarDoctorPhaseOutTriggeredAbility(final TheWarDoctorPhaseOutTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public TheWarDoctorPhaseOutTriggeredAbility copy() {
        return new TheWarDoctorPhaseOutTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.PHASED_OUT_BATCH;
    }

    @Override
    public boolean checkEvent(GameEvent event, Game game) {
        return !event.getTargetId().equals(getSourceId());
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        return !getFilteredEvents((PhasedOutBatchEvent) event, game).isEmpty();
    }
}

class TheWarDoctorExileTriggeredAbility extends TriggeredAbilityImpl implements BatchTriggeredAbility<ZoneChangeEvent> {

    TheWarDoctorExileTriggeredAbility() {
        super(Zone.BATTLEFIELD, new AddCountersSourceEffect(CounterType.TIME.createInstance()), false);
        setTriggerPhrase("Whenever one or more other cards are put into exile from anywhere, ");
    }

    private TheWarDoctorExileTriggeredAbility(final TheWarDoctorExileTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public TheWarDoctorExileTriggeredAbility copy() {
        return new TheWarDoctorExileTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.ZONE_CHANGE_BATCH;
    }

    @Override
    public boolean checkEvent(ZoneChangeEvent event, Game game) {
        // a token is not a card
        return Zone.EXILED.match(event.getToZone())
                && !event.getTargetId().equals(getSourceId())
                && game.getCard(event.getTargetId()) != null;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        return !getFilteredEvents((ZoneChangeBatchEvent) event, game).isEmpty();
    }
}
