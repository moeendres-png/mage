package mage.cards.i;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.effects.ContinuousEffect;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.RestrictionEffect;
import mage.abilities.effects.common.combat.GoadTargetEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.counters.Counters;
import mage.filter.common.FilterCreatureCard;
import mage.target.targetpointer.FixedTarget;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.common.TargetCardInOpponentsGraveyard;

import java.util.UUID;

/**
 * Immortal Obligation {1}{W} instant
 * Return target creature card from an opponent's graveyard to the battlefield under their control with a duty
 * counter on it. For as long as that creature has a duty counter on it, it is goaded, can't attack you or a
 * permanent you control, and can't block creatures you control.
 */
public final class ImmortalObligation extends CardImpl {

    public ImmortalObligation(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.INSTANT}, "{1}{W}");

        // Return target creature card from an opponent's graveyard to the battlefield under their control with a duty counter on it.
        // For as long as that creature has a duty counter on it, it is goaded, can't attack you or a permanent you control,
        // and can't block creatures you control.
        this.getSpellAbility().addEffect(new ImmortalObligationEffect());
        this.getSpellAbility().addTarget(new TargetCardInOpponentsGraveyard(new FilterCreatureCard("creature card from an opponent's graveyard")));
    }

    private ImmortalObligation(final ImmortalObligation card) {
        super(card);
    }

    @Override
    public ImmortalObligation copy() {
        return new ImmortalObligation(this);
    }
}

class ImmortalObligationEffect extends OneShotEffect {

    ImmortalObligationEffect() {
        super(Outcome.Detriment);
        staticText = "return target creature card from an opponent's graveyard to the battlefield under their control "
                + "with a duty counter on it. For as long as that creature has a duty counter on it, it is goaded, "
                + "can't attack you or a permanent you control, and can't block creatures you control";
    }

    private ImmortalObligationEffect(final ImmortalObligationEffect effect) {
        super(effect);
    }

    @Override
    public ImmortalObligationEffect copy() {
        return new ImmortalObligationEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Card card = game.getCard(getTargetPointer().getFirst(game, source));
        if (card == null || game.getState().getZone(card.getId()) != Zone.GRAVEYARD) {
            return false;
        }
        Player owner = game.getPlayer(card.getOwnerId());
        if (owner == null) {
            return false;
        }
        Counters counters = new Counters();
        counters.addCounter(CounterType.DUTY.createInstance());
        game.setEnterWithCounters(card.getId(), counters);
        owner.moveCards(card, Zone.BATTLEFIELD, source, game);
        Permanent permanent = game.getPermanent(card.getId());
        if (permanent == null) {
            return true;
        }
        MageObjectReference duty = new MageObjectReference(permanent, game);
        game.addEffect(new ImmortalObligationGoadEffect(duty), source);
        game.addEffect(new ImmortalObligationRestrictionEffect(duty), source);
        return true;
    }
}

class ImmortalObligationGoadEffect extends GoadTargetEffect {

    private final MageObjectReference duty;

    ImmortalObligationGoadEffect(MageObjectReference duty) {
        super(Duration.Custom);
        this.duty = duty;
        this.setTargetPointer(new FixedTarget(duty));
    }

    private ImmortalObligationGoadEffect(final ImmortalObligationGoadEffect effect) {
        super(effect);
        this.duty = effect.duty;
    }

    @Override
    public ImmortalObligationGoadEffect copy() {
        return new ImmortalObligationGoadEffect(this);
    }

    @Override
    public boolean isInactive(Ability source, Game game) {
        return ImmortalObligationRestrictionEffect.dutyEnded(duty, game);
    }
}

class ImmortalObligationRestrictionEffect extends RestrictionEffect {

    private final MageObjectReference duty;

    ImmortalObligationRestrictionEffect(MageObjectReference duty) {
        super(Duration.Custom);
        this.duty = duty;
        staticText = "it can't attack you or a permanent you control and can't block creatures you control";
    }

    private ImmortalObligationRestrictionEffect(final ImmortalObligationRestrictionEffect effect) {
        super(effect);
        this.duty = effect.duty;
    }

    @Override
    public ImmortalObligationRestrictionEffect copy() {
        return new ImmortalObligationRestrictionEffect(this);
    }

    static boolean dutyEnded(MageObjectReference duty, Game game) {
        Permanent permanent = duty.getPermanent(game);
        return permanent == null || permanent.getCounters(game).getCount(CounterType.DUTY) == 0;
    }

    @Override
    public boolean isInactive(Ability source, Game game) {
        return dutyEnded(duty, game);
    }

    @Override
    public boolean applies(Permanent permanent, Ability source, Game game) {
        return duty.refersTo(permanent, game);
    }

    @Override
    public boolean canAttack(Permanent attacker, UUID defenderId, Ability source, Game game, boolean canUseChooseDialogs) {
        if (defenderId == null) {
            return true;
        }
        if (defenderId.equals(source.getControllerId())) {
            return false;
        }
        Permanent defendingPermanent = game.getPermanent(defenderId);
        return defendingPermanent == null || !defendingPermanent.isControlledBy(source.getControllerId());
    }

    @Override
    public boolean canBlock(Permanent attacker, Permanent blocker, Ability source, Game game, boolean canUseChooseDialogs) {
        return !attacker.isControlledBy(source.getControllerId());
    }
}
