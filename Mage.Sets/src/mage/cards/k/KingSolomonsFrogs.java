package mage.cards.k;

import mage.abilities.hint.common.MonarchHint;
import mage.abilities.Ability;
import mage.abilities.common.EntersBattlefieldTriggeredAbility;
import mage.abilities.common.SimpleActivatedAbility;
import mage.abilities.condition.common.CastFromEverywhereSourceCondition;
import mage.abilities.costs.common.ExileSourceCost;
import mage.abilities.costs.common.TapSourceCost;
import mage.abilities.costs.mana.GenericManaCost;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.BecomesMonarchSourceEffect;
import mage.abilities.keyword.FlashAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.ComparisonType;
import mage.constants.Outcome;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.FilterPermanent;
import mage.filter.predicate.mageobject.ManaValuePredicate;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.TargetPermanent;
import mage.target.targetadjustment.ForEachPlayerTargetsAdjuster;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * @author commander-lab
 */
public final class KingSolomonsFrogs extends CardImpl {

    private static final FilterPermanent filter = new FilterPermanent("permanent with mana value 3 or greater");

    static {
        filter.add(new ManaValuePredicate(ComparisonType.MORE_THAN, 2));
    }

    public KingSolomonsFrogs(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT}, "{3}{W}");

        this.supertype.add(SuperType.LEGENDARY);

        // Flash
        this.addAbility(FlashAbility.getInstance());

        // When King Solomon's Frogs enters, if you cast it, for each opponent, exile up to one target permanent that player controls with mana value 3 or greater. For each permanent exiled this way, its controller draws a card.
        Ability ability = new EntersBattlefieldTriggeredAbility(new KingSolomonsFrogsEffect())
                .withInterveningIf(CastFromEverywhereSourceCondition.instance);
        ability.addTarget(new TargetPermanent(0, 1, filter));
        ability.setTargetAdjuster(new ForEachPlayerTargetsAdjuster(false, true));
        this.addAbility(ability);

        // {3}, {T}, Exile King Solomon's Frogs: You become the monarch.
        ability = new SimpleActivatedAbility(new BecomesMonarchSourceEffect(), new GenericManaCost(3));
        ability.addCost(new TapSourceCost());
        ability.addCost(new ExileSourceCost());
        ability.addHint(MonarchHint.instance);
        this.addAbility(ability);
    }

    private KingSolomonsFrogs(final KingSolomonsFrogs card) {
        super(card);
    }

    @Override
    public KingSolomonsFrogs copy() {
        return new KingSolomonsFrogs(this);
    }
}

class KingSolomonsFrogsEffect extends OneShotEffect {

    KingSolomonsFrogsEffect() {
        super(Outcome.Exile);
        staticText = "for each opponent, exile up to one target permanent that player controls with mana value "
                + "3 or greater. For each permanent exiled this way, its controller draws a card";
    }

    private KingSolomonsFrogsEffect(final KingSolomonsFrogsEffect effect) {
        super(effect);
    }

    @Override
    public KingSolomonsFrogsEffect copy() {
        return new KingSolomonsFrogsEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        List<UUID> drawers = new ArrayList<>();
        for (mage.target.Target target : source.getTargets()) {
            for (UUID targetId : target.getTargets()) {
                Permanent permanent = game.getPermanent(targetId);
                if (permanent == null) {
                    continue;
                }
                UUID controllerId = permanent.getControllerId();
                boolean token = permanent instanceof mage.game.permanent.PermanentToken;
                controller.moveCards(permanent, Zone.EXILED, source, game);
                // a token is exiled too, even though it then ceases to exist
                if (game.getState().getZone(targetId) == Zone.EXILED
                        || token && game.getPermanent(targetId) == null) {
                    drawers.add(controllerId);
                }
            }
        }
        for (UUID playerId : drawers) {
            Player player = game.getPlayer(playerId);
            if (player != null) {
                player.drawCards(1, source, game);
            }
        }
        return true;
    }
}
