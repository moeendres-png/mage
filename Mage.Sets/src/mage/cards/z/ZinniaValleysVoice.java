package mage.cards.z;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.SpellAbility;
import mage.abilities.StaticAbility;
import mage.abilities.common.EntersBattlefieldTriggeredAbility;
import mage.abilities.condition.Condition;
import mage.abilities.costs.OptionalAdditionalCost;
import mage.abilities.costs.OptionalAdditionalCostImpl;
import mage.abilities.costs.OptionalAdditionalSourceCosts;
import mage.abilities.costs.mana.ManaCostsImpl;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.CreateTokenCopyTargetEffect;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.util.CardUtil;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.dynamicvalue.common.PermanentsOnBattlefieldCount;
import mage.abilities.effects.common.continuous.BoostSourceEffect;
import mage.abilities.effects.common.continuous.GainAbilityControlledSpellsEffect;
import mage.abilities.dynamicvalue.common.StaticValue;
import mage.abilities.keyword.FlyingAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.ComparisonType;
import mage.constants.Duration;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.CardType;
import mage.filter.FilterCard;
import mage.filter.common.FilterControlledCreaturePermanent;
import mage.filter.predicate.mageobject.AnotherPredicate;
import mage.filter.predicate.mageobject.BasePowerPredicate;

import java.util.UUID;

/**
 * @author Claude
 */
public final class ZinniaValleysVoice extends CardImpl {

    private static final FilterControlledCreaturePermanent filter
            = new FilterControlledCreaturePermanent("other creatures you control with base power 1");
    private static final FilterCard spellFilter = new FilterCard("creature spells you cast");

    static {
        filter.add(AnotherPredicate.instance);
        filter.add(new BasePowerPredicate(ComparisonType.EQUAL_TO, 1));
        spellFilter.add(CardType.CREATURE.getPredicate());
    }

    public ZinniaValleysVoice(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{U}{R}{W}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.BIRD);
        this.subtype.add(SubType.BARD);
        this.power = new MageInt(1);
        this.toughness = new MageInt(3);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // Zinnia gets +X/+0, where X is the number of other creatures you control with base power 1.
        this.addAbility(new SimpleStaticAbility(new BoostSourceEffect(
                new PermanentsOnBattlefieldCount(filter), StaticValue.get(0), Duration.WhileOnBattlefield
        )));

        // Creature spells you cast gain offspring {2} as you cast them.
        this.addAbility(new SimpleStaticAbility(new GainAbilityControlledSpellsEffect(
                new ZinniaOffspringAbility(), spellFilter, null, true
        )));
    }

    private ZinniaValleysVoice(final ZinniaValleysVoice card) {
        super(card);
    }

    @Override
    public ZinniaValleysVoice copy() {
        return new ZinniaValleysVoice(this);
    }
}

/**
 * Offspring {2} as granted by Zinnia. Behaves like the keyword, but asks for the additional cost only once per cast:
 * while a spell is being cast the granting effect can leave more than one copy of the granted ability on the spell
 * (the effect itself and its bridge to the permanent), and each copy would ask on its own.
 */
class ZinniaOffspringAbility extends StaticAbility implements OptionalAdditionalSourceCosts {

    private static final String KEY = "offspringActivation";
    private static final String ASKED_KEY = "ZinniaOffspringAsked";
    private static final String REMINDER = "You may pay an additional {2} as you cast this spell. "
            + "If you do, when this creature enters, create a 1/1 token copy of it.";

    private final OptionalAdditionalCost additionalCost;

    ZinniaOffspringAbility() {
        super(Zone.STACK, null);
        this.additionalCost = new OptionalAdditionalCostImpl("Offspring {2}", REMINDER, new ManaCostsImpl<>("{2}"));
        this.additionalCost.setRepeatable(false);
        this.setRuleAtTheTop(true);
        this.addSubAbility(new EntersBattlefieldTriggeredAbility(new ZinniaOffspringEffect())
                .withInterveningIf(ZinniaOffspringCondition.instance).setRuleVisible(false));
    }

    private ZinniaOffspringAbility(final ZinniaOffspringAbility ability) {
        super(ability);
        this.additionalCost = ability.additionalCost.copy();
    }

    @Override
    public ZinniaOffspringAbility copy() {
        return new ZinniaOffspringAbility(this);
    }

    @Override
    public void addOptionalAdditionalCosts(Ability ability, Game game) {
        if (!(ability instanceof SpellAbility)) {
            return;
        }
        Player player = game.getPlayer(ability.getControllerId());
        if (player == null) {
            return;
        }
        String askedKey = ASKED_KEY + ability.getId();
        if (game.getState().getValue(askedKey) != null) {
            return;
        }
        game.getState().setValue(askedKey, true);
        additionalCost.reset();
        if (!additionalCost.canPay(ability, this, ability.getControllerId(), game)
                || !player.chooseUse(Outcome.PutCreatureInPlay, "Pay " + additionalCost.getText(true) + " for offspring?", ability, game)) {
            return;
        }
        additionalCost.activate();
        ability.addCost(additionalCost.copy());
        CardUtil.setSourceCostsTag(game, ability, KEY, null);
    }

    @Override
    public String getCastMessageSuffix() {
        return additionalCost.getCastSuffixMessage(0);
    }

    @Override
    public String getRule() {
        return additionalCost.getName() + ' ' + additionalCost.getReminderText();
    }
}

class ZinniaOffspringEffect extends OneShotEffect {

    ZinniaOffspringEffect() {
        super(Outcome.Benefit);
        staticText = "create a 1/1 token copy of it";
    }

    private ZinniaOffspringEffect(final ZinniaOffspringEffect effect) {
        super(effect);
    }

    @Override
    public ZinniaOffspringEffect copy() {
        return new ZinniaOffspringEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent permanent = source.getSourcePermanentOrLKI(game);
        return permanent != null && new CreateTokenCopyTargetEffect(
                null, null, false, 1, false,
                false, null, 1, 1, false
        ).setSavedPermanent(permanent).apply(game, source);
    }
}

enum ZinniaOffspringCondition implements Condition {
    instance;

    @Override
    public boolean apply(Game game, Ability source) {
        return CardUtil.checkSourceCostsTagExists(game, source, "offspringActivation");
    }

    @Override
    public String toString() {
        return "its offspring cost was paid";
    }
}
