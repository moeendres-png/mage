package mage.cards.j;

import mage.abilities.Ability;
import mage.abilities.LoyaltyAbility;
import mage.abilities.common.CanBeYourCommanderAbility;
import mage.abilities.costs.Cost;
import mage.abilities.costs.mana.ManaCostsImpl;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.RestrictionEffect;
import mage.abilities.effects.common.DrawCardSourceControllerEffect;
import mage.abilities.triggers.BeginningOfCombatTriggeredAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.TargetController;
import mage.constants.Zone;
import mage.filter.common.FilterControlledPermanent;
import mage.filter.predicate.Predicates;
import mage.filter.predicate.mageobject.AnotherPredicate;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.TargetCard;
import mage.target.common.TargetCardInHand;
import mage.target.common.TargetControlledPermanent;

import java.util.UUID;

/**
 * @author Claude
 */
public final class JaceMultiverseArchitect extends CardImpl {

    private static final FilterControlledPermanent filter
            = new FilterControlledPermanent("another planeswalker or creature you control");

    static {
        filter.add(AnotherPredicate.instance);
        filter.add(Predicates.or(CardType.CREATURE.getPredicate(), CardType.PLANESWALKER.getPredicate()));
    }

    public JaceMultiverseArchitect(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.PLANESWALKER}, "{1}{W}{U}{B}{R}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.JACE);
        this.setStartingLoyalty(4);

        // At the beginning of combat on each opponent's turn, they may pay {2}. If they don't,
        // creatures they control can't attack Jaces you control this turn.
        this.addAbility(new BeginningOfCombatTriggeredAbility(
                TargetController.OPPONENT, new JaceMultiverseArchitectPayEffect(), false
        ));

        // +1: Draw two cards, then put a card from your hand on the bottom of your library.
        Ability ability = new LoyaltyAbility(new DrawCardSourceControllerEffect(2), 1);
        ability.addEffect(new JaceMultiverseArchitectBottomEffect());
        this.addAbility(ability);

        // -3: Exile another target planeswalker or creature you control. Reveal cards from the top of your library
        // until you reveal a creature or planeswalker card. Put that card onto the battlefield and the rest on
        // the bottom of your library in a random order.
        ability = new LoyaltyAbility(new JaceMultiverseArchitectExileEffect(), -3);
        ability.addTarget(new TargetControlledPermanent(filter));
        this.addAbility(ability);

        // Jace, Multiverse Architect can be your commander.
        this.addAbility(CanBeYourCommanderAbility.getInstance());
    }

    private JaceMultiverseArchitect(final JaceMultiverseArchitect card) {
        super(card);
    }

    @Override
    public JaceMultiverseArchitect copy() {
        return new JaceMultiverseArchitect(this);
    }
}

class JaceMultiverseArchitectPayEffect extends OneShotEffect {

    JaceMultiverseArchitectPayEffect() {
        super(Outcome.Detriment);
        staticText = "they may pay {2}. If they don't, creatures they control can't attack Jaces you control this turn";
    }

    private JaceMultiverseArchitectPayEffect(final JaceMultiverseArchitectPayEffect effect) {
        super(effect);
    }

    @Override
    public JaceMultiverseArchitectPayEffect copy() {
        return new JaceMultiverseArchitectPayEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player player = game.getPlayer(getTargetPointer().getFirst(game, source));
        if (player == null) {
            return false;
        }
        Cost cost = new ManaCostsImpl<>("{2}");
        if (cost.canPay(source, source, player.getId(), game)
                && player.chooseUse(Outcome.Detriment, "Pay {2} so your creatures can attack Jaces?", source, game)) {
            cost.clearPaid();
            if (cost.pay(source, game, source, player.getId(), false, null)) {
                game.informPlayers(player.getLogName() + " pays {2} to prevent the effect");
                return true;
            }
        }
        game.addEffect(new JaceMultiverseArchitectRestrictionEffect(player.getId()), source);
        return true;
    }
}

class JaceMultiverseArchitectRestrictionEffect extends RestrictionEffect {

    private final UUID attackerControllerId;

    JaceMultiverseArchitectRestrictionEffect(UUID attackerControllerId) {
        super(Duration.EndOfTurn);
        this.attackerControllerId = attackerControllerId;
        staticText = "creatures they control can't attack Jaces you control this turn";
    }

    private JaceMultiverseArchitectRestrictionEffect(final JaceMultiverseArchitectRestrictionEffect effect) {
        super(effect);
        this.attackerControllerId = effect.attackerControllerId;
    }

    @Override
    public JaceMultiverseArchitectRestrictionEffect copy() {
        return new JaceMultiverseArchitectRestrictionEffect(this);
    }

    @Override
    public boolean applies(Permanent permanent, Ability source, Game game) {
        return permanent.isControlledBy(attackerControllerId);
    }

    @Override
    public boolean canAttack(Permanent attacker, UUID defenderId, Ability source, Game game, boolean canUseChooseDialogs) {
        if (defenderId == null) {
            return true;
        }
        Permanent defender = game.getPermanent(defenderId);
        return defender == null
                || !defender.isPlaneswalker(game)
                || !defender.hasSubtype(SubType.JACE, game)
                || !defender.isControlledBy(source.getControllerId());
    }
}

class JaceMultiverseArchitectBottomEffect extends OneShotEffect {

    JaceMultiverseArchitectBottomEffect() {
        super(Outcome.Discard);
        staticText = ", then put a card from your hand on the bottom of your library";
    }

    private JaceMultiverseArchitectBottomEffect(final JaceMultiverseArchitectBottomEffect effect) {
        super(effect);
    }

    @Override
    public JaceMultiverseArchitectBottomEffect copy() {
        return new JaceMultiverseArchitectBottomEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null || controller.getHand().isEmpty()) {
            return false;
        }
        TargetCard target = new TargetCardInHand();
        target.withNotTarget(true);
        controller.chooseTarget(Outcome.Discard, controller.getHand(), target, source, game);
        Card card = game.getCard(target.getFirstTarget());
        return card != null && controller.putCardsOnBottomOfLibrary(card, game, source);
    }
}

class JaceMultiverseArchitectExileEffect extends OneShotEffect {

    JaceMultiverseArchitectExileEffect() {
        super(Outcome.PutCreatureInPlay);
        staticText = "exile another target planeswalker or creature you control. Reveal cards from the top of your "
                + "library until you reveal a creature or planeswalker card. Put that card onto the battlefield "
                + "and the rest on the bottom of your library in a random order";
    }

    private JaceMultiverseArchitectExileEffect(final JaceMultiverseArchitectExileEffect effect) {
        super(effect);
    }

    @Override
    public JaceMultiverseArchitectExileEffect copy() {
        return new JaceMultiverseArchitectExileEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        Permanent permanent = game.getPermanent(getTargetPointer().getFirst(game, source));
        if (permanent != null) {
            controller.moveCards(permanent, Zone.EXILED, source, game);
        }
        Cards revealed = new CardsImpl();
        Card found = null;
        for (Card card : controller.getLibrary().getCards(game)) {
            revealed.add(card);
            if (card.isCreature(game) || card.isPlaneswalker(game)) {
                found = card;
                break;
            }
        }
        controller.revealCards(source, revealed, game);
        if (found != null) {
            controller.moveCards(found, Zone.BATTLEFIELD, source, game);
            revealed.remove(found);
        }
        revealed.retainZone(Zone.LIBRARY, game);
        controller.putCardsOnBottomOfLibrary(revealed, game, source, false);
        return true;
    }
}
