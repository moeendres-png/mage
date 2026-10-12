package mage.cards.h;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.common.DealtDamageToSourceTriggeredAbility;
import mage.abilities.dynamicvalue.common.SavedDamageValue;
import mage.abilities.effects.common.continuous.GainAbilitySourceEffect;
import mage.abilities.effects.common.counter.AddCountersSourceEffect;
import mage.abilities.keyword.IndestructibleAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.counters.CounterType;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class HerculesOlympianHero extends CardImpl {

    public HerculesOlympianHero(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{3}{W}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.DEMIGOD);
        this.subtype.add(SubType.WARRIOR);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(3);
        this.toughness = new MageInt(3);

        // Whenever Hercules attacks, put a +1/+1 counter on him. He gains indestructible until end of turn.
        Ability ability = new AttacksTriggeredAbility(new AddCountersSourceEffect(CounterType.P1P1.createInstance())
                .setText("put a +1/+1 counter on him"));
        ability.addEffect(new GainAbilitySourceEffect(IndestructibleAbility.getInstance(), Duration.EndOfTurn)
                .setText("He gains indestructible until end of turn"));
        this.addAbility(ability);

        // Whenever Hercules is dealt damage for the first time each turn, put that many +1/+1 counters on him.
        this.addAbility(new DealtDamageToSourceTriggeredAbility(new AddCountersSourceEffect(
                CounterType.P1P1.createInstance(0), SavedDamageValue.MANY
        ).setText("put that many +1/+1 counters on him"), false)
                .setTriggerPhrase("Whenever {this} is dealt damage for the first time each turn, ")
                .setTriggersLimitEachTurn(1));
    }

    private HerculesOlympianHero(final HerculesOlympianHero card) {
        super(card);
    }

    @Override
    public HerculesOlympianHero copy() {
        return new HerculesOlympianHero(this);
    }
}
