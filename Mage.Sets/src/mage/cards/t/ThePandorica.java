package mage.cards.t;

import mage.abilities.Ability;
import mage.abilities.common.SimpleActivatedAbility;
import mage.abilities.common.SkipUntapOptionalAbility;
import mage.abilities.costs.common.TapSourceCost;
import mage.abilities.costs.mana.ManaCostsImpl;
import mage.abilities.effects.common.PhaseOutHeldBySourceEffect;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.SuperType;
import mage.constants.TimingRule;
import mage.filter.FilterPermanent;
import mage.filter.common.FilterNonlandPermanent;
import mage.filter.predicate.mageobject.AnotherPredicate;
import mage.target.TargetPermanent;

import java.util.UUID;

/**
 * The Pandorica {2}{W}
 * Legendary Artifact
 * You may choose not to untap The Pandorica during your untap step.
 * {1}{W}, {T}: Untap another target nonland permanent, then it phases out. It can't phase in for as long as
 * The Pandorica remains tapped. When The Pandorica becomes untapped or leaves the battlefield, that permanent
 * phases in. Activate only as a sorcery.
 */
public final class ThePandorica extends CardImpl {

    private static final FilterPermanent filter = new FilterNonlandPermanent("another target nonland permanent");

    static {
        filter.add(AnotherPredicate.instance);
    }

    public ThePandorica(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT}, "{2}{W}");

        this.supertype.add(SuperType.LEGENDARY);

        // You may choose not to untap The Pandorica during your untap step.
        this.addAbility(new SkipUntapOptionalAbility());

        // {1}{W}, {T}: Untap another target nonland permanent, then it phases out. It can't phase in for as long as
        // The Pandorica remains tapped. When The Pandorica becomes untapped or leaves the battlefield, that permanent
        // phases in. Activate only as a sorcery.
        Ability ability = new SimpleActivatedAbility(
                new PhaseOutHeldBySourceEffect(true), new ManaCostsImpl<>("{1}{W}")
        ).setTiming(TimingRule.SORCERY);
        ability.addCost(new TapSourceCost());
        ability.addTarget(new TargetPermanent(filter));
        this.addAbility(ability);
    }

    private ThePandorica(final ThePandorica card) {
        super(card);
    }

    @Override
    public ThePandorica copy() {
        return new ThePandorica(this);
    }
}
