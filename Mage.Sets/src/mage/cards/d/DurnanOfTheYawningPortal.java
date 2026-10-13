package mage.cards.d;

import mage.MageInt;
import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.SpellAbility;
import mage.abilities.common.AttacksTriggeredAbility;
import mage.abilities.common.ChooseABackgroundAbility;
import mage.abilities.dynamicvalue.common.OpponentsCount;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.cost.CostModificationEffectImpl;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.CardType;
import mage.constants.CostModificationType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.players.Player;
import mage.target.TargetCard;
import mage.util.CardUtil;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class DurnanOfTheYawningPortal extends CardImpl {

    public DurnanOfTheYawningPortal(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{3}{G}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.WARRIOR);
        this.power = new MageInt(3);
        this.toughness = new MageInt(3);

        // Whenever Durnan attacks, look at the top four cards of your library. You may exile a creature card from among them. Put the rest on the bottom of your library in any order. For as long as that card remains exiled, you may cast it. That spell has undaunted.
        this.addAbility(new AttacksTriggeredAbility(new DurnanOfTheYawningPortalEffect()));

        // Choose a Background
        this.addAbility(ChooseABackgroundAbility.getInstance());
    }

    private DurnanOfTheYawningPortal(final DurnanOfTheYawningPortal card) {
        super(card);
    }

    @Override
    public DurnanOfTheYawningPortal copy() {
        return new DurnanOfTheYawningPortal(this);
    }
}

class DurnanOfTheYawningPortalEffect extends OneShotEffect {

    DurnanOfTheYawningPortalEffect() {
        super(Outcome.PlayForFree);
        staticText = "look at the top four cards of your library. You may exile a creature card from among them. "
                + "Put the rest on the bottom of your library in any order. For as long as that card remains "
                + "exiled, you may cast it. That spell has undaunted. <i>(It costs {1} less to cast for each opponent.)</i>";
    }

    private DurnanOfTheYawningPortalEffect(final DurnanOfTheYawningPortalEffect effect) {
        super(effect);
    }

    @Override
    public DurnanOfTheYawningPortalEffect copy() {
        return new DurnanOfTheYawningPortalEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        Cards cards = new CardsImpl(controller.getLibrary().getTopCards(game, 4));
        if (cards.isEmpty()) {
            return false;
        }
        TargetCard target = new TargetCard(0, 1, Zone.LIBRARY, StaticFilters.FILTER_CARD_CREATURE);
        target.withChooseHint("to exile; you may cast it while it remains exiled");
        controller.choose(Outcome.PlayForFree, cards, target, source, game);
        Card card = game.getCard(target.getFirstTarget());
        if (card != null) {
            controller.moveCardsToExile(card, source, game, true,
                    CardUtil.getExileZoneId(game, source), CardUtil.getSourceName(game, source));
            cards.remove(card);
            if (game.getState().getZone(card.getId()) == Zone.EXILED) {
                CardUtil.makeCardPlayable(game, source, card, true, Duration.Custom, false);
                game.addEffect(new DurnanOfTheYawningPortalCostEffect(new MageObjectReference(card, game)), source);
            }
        }
        controller.putCardsOnBottomOfLibrary(cards, game, source, true);
        return true;
    }
}

/**
 * "That spell has undaunted": the card cast from the exile zone it was put into costs {1} less for
 * each opponent. Ends once the card leaves that exile zone without being cast from it.
 */
class DurnanOfTheYawningPortalCostEffect extends CostModificationEffectImpl {

    private final MageObjectReference mor;

    DurnanOfTheYawningPortalCostEffect(MageObjectReference mor) {
        super(Duration.Custom, Outcome.Benefit, CostModificationType.REDUCE_COST);
        this.mor = mor;
        staticText = "that spell has undaunted";
    }

    private DurnanOfTheYawningPortalCostEffect(final DurnanOfTheYawningPortalCostEffect effect) {
        super(effect);
        this.mor = effect.mor;
    }

    @Override
    public DurnanOfTheYawningPortalCostEffect copy() {
        return new DurnanOfTheYawningPortalCostEffect(this);
    }

    @Override
    public boolean isInactive(Ability source, Game game) {
        // the exiled object, or the spell cast from it (one zone change later), is still around
        int zcc = game.getState().getZoneChangeCounter(mor.getSourceId());
        return zcc != mor.getZoneChangeCounter() && zcc != mor.getZoneChangeCounter() + 1;
    }

    @Override
    public boolean applies(Ability abilityToModify, Ability source, Game game) {
        if (!(abilityToModify instanceof SpellAbility)
                || !abilityToModify.isControlledBy(source.getControllerId())
                || !mor.getSourceId().equals(abilityToModify.getSourceId())) {
            return false;
        }
        int zcc = game.getState().getZoneChangeCounter(mor.getSourceId());
        Zone zone = game.getState().getZone(mor.getSourceId());
        return zcc == mor.getZoneChangeCounter() && zone == Zone.EXILED
                || zcc == mor.getZoneChangeCounter() + 1 && zone == Zone.STACK;
    }

    @Override
    public boolean apply(Game game, Ability source, Ability abilityToModify) {
        CardUtil.reduceCost(abilityToModify, OpponentsCount.instance.calculate(game, source, this));
        return true;
    }
}
