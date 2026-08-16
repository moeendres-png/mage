package mage.cards.a;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.SacrificePermanentTriggeredAbility;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.common.delayed.AtTheBeginOfNextEndStepDelayedTriggeredAbility;
import mage.abilities.costs.mana.ManaCostsImpl;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.CreateTokenCopyTargetEffect;
import mage.abilities.effects.common.DoUnlessControllerPaysEffect;
import mage.abilities.effects.common.SacrificeTargetEffect;
import mage.abilities.effects.common.continuous.GainAbilityControlledSpellsEffect;
import mage.abilities.effects.common.continuous.GainAbilityTargetEffect;
import mage.abilities.keyword.EvokeAbility;
import mage.abilities.keyword.HasteAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.*;
import mage.filter.FilterPermanent;
import mage.filter.common.FilterPermanentCard;
import mage.filter.predicate.permanent.TokenPredicate;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.target.targetpointer.FixedTargets;

import java.util.List;
import java.util.UUID;

/**
 * @author
 */
public final class AshlingTheLimitless extends CardImpl {

    private static final FilterPermanentCard spellFilter =
            new FilterPermanentCard(
                    "Elemental permanent spells you cast from your hand"
            );

    private static final FilterPermanent sacrificeFilter =
            new FilterPermanent("nontoken Elemental");

    static {
        spellFilter.add(SubType.ELEMENTAL.getPredicate());

        sacrificeFilter.add(SubType.ELEMENTAL.getPredicate());
        sacrificeFilter.add(TokenPredicate.FALSE);
    }

    public AshlingTheLimitless(UUID ownerId, CardSetInfo setInfo) {
        super(
                ownerId,
                setInfo,
                new CardType[]{CardType.CREATURE},
                "{2}{R}"
        );

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.ELEMENTAL);
        this.subtype.add(SubType.SORCERER);
        this.power = new MageInt(2);
        this.toughness = new MageInt(3);

        // Elemental permanent spells you cast from your hand gain
        // evoke {4} as you cast them.
        this.addAbility(
                new SimpleStaticAbility(
                        new GainAbilityControlledSpellsEffect(
                                new EvokeAbility("{4}"),
                                spellFilter,
                                Zone.HAND,
                                true
                        )
                )
        );

        // Whenever you sacrifice a nontoken Elemental, create a token
        // that's a copy of it. The token gains haste until end of turn.
        // At the beginning of your next end step, sacrifice it unless
        // you pay {W}{U}{B}{R}{G}.
        this.addAbility(
                new SacrificePermanentTriggeredAbility(
                        new AshlingTheLimitlessCopyEffect(),
                        sacrificeFilter
                )
        );
    }

    private AshlingTheLimitless(final AshlingTheLimitless card) {
        super(card);
    }

    @Override
    public AshlingTheLimitless copy() {
        return new AshlingTheLimitless(this);
    }
}

class AshlingTheLimitlessCopyEffect extends OneShotEffect {

    AshlingTheLimitlessCopyEffect() {
        super(Outcome.Benefit);
        staticText = "create a token that's a copy of it. "
                + "The token gains haste until end of turn. "
                + "At the beginning of your next end step, "
                + "sacrifice it unless you pay {W}{U}{B}{R}{G}";
    }

    private AshlingTheLimitlessCopyEffect(
            final AshlingTheLimitlessCopyEffect effect
    ) {
        super(effect);
    }

    @Override
    public AshlingTheLimitlessCopyEffect copy() {
        return new AshlingTheLimitlessCopyEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent sacrificedPermanent =
                (Permanent) getValue("sacrificedPermanent");

        if (sacrificedPermanent == null) {
            return false;
        }

        // Copy the sacrificed permanent from LKI/copiable values.
        CreateTokenCopyTargetEffect copyEffect =
                new CreateTokenCopyTargetEffect();

        copyEffect.setSavedPermanent(sacrificedPermanent);

        if (!copyEffect.apply(game, source)) {
            return false;
        }

        List<Permanent> tokens = copyEffect.getAddedPermanents();

        if (tokens.isEmpty()) {
            return false;
        }

        // "The token gains haste until end of turn."
        GainAbilityTargetEffect hasteEffect =
                new GainAbilityTargetEffect(
                        HasteAbility.getInstance(),
                        Duration.EndOfTurn
                );

        hasteEffect.setTargetPointer(
                new FixedTargets(tokens, game)
        );

        game.addEffect(hasteEffect, source);

        // "At the beginning of your next end step,
        // sacrifice it unless you pay {W}{U}{B}{R}{G}."
        SacrificeTargetEffect sacrificeEffect =
                new SacrificeTargetEffect(
                        "sacrifice it",
                        source.getControllerId()
                );

        DoUnlessControllerPaysEffect sacrificeUnlessPaid =
                new DoUnlessControllerPaysEffect(
                        sacrificeEffect,
                        new ManaCostsImpl<>("{W}{U}{B}{R}{G}"),
                        "Pay {W}{U}{B}{R}{G}?"
                );

        sacrificeUnlessPaid.setTargetPointer(
                new FixedTargets(tokens, game)
        );

        game.addDelayedTriggeredAbility(
                new AtTheBeginOfNextEndStepDelayedTriggeredAbility(
                        sacrificeUnlessPaid,
                        TargetController.YOU
                ),
                source
        );

        return true;
    }
}
