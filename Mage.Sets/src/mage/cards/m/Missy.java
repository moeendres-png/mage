package mage.cards.m;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.DiesCreatureTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.FaceVillainousChoiceOpponentsEffect;
import mage.abilities.effects.keyword.CybermanFaceDown;
import mage.abilities.triggers.BeginningOfEndStepTriggeredAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.choices.FaceVillainousChoice;
import mage.choices.VillainousChoice;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.common.FilterControlledPermanent;
import mage.filter.common.FilterCreaturePermanent;
import mage.filter.predicate.Predicates;
import mage.filter.predicate.mageobject.AnotherPredicate;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;

import java.util.Collections;
import java.util.UUID;

/**
 * @author Claude
 */
public final class Missy extends CardImpl {

    private static final FilterCreaturePermanent filter = new FilterCreaturePermanent("another nonartifact creature");
    private static final FaceVillainousChoice choice = new FaceVillainousChoice(
            Outcome.Damage, new MissyFirstChoice(), new MissySecondChoice()
    );

    static {
        filter.add(AnotherPredicate.instance);
        filter.add(Predicates.not(CardType.ARTIFACT.getPredicate()));
    }

    public Missy(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{3}{U}{B}{R}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.TIME_LORD);
        this.subtype.add(SubType.ROGUE);
        this.power = new MageInt(4);
        this.toughness = new MageInt(5);

        // Whenever another nonartifact creature dies, return it to the battlefield under your control face down and tapped. It's a 2/2 Cyberman artifact creature.
        this.addAbility(new DiesCreatureTriggeredAbility(new MissyReturnEffect(), false, filter, true));

        // At the beginning of your end step, each opponent faces a villainous choice -- Each artifact creature you control deals 1 damage to that opponent, or you draw a card and chaos ensues.
        this.addAbility(new BeginningOfEndStepTriggeredAbility(new FaceVillainousChoiceOpponentsEffect(choice)));
    }

    private Missy(final Missy card) {
        super(card);
    }

    @Override
    public Missy copy() {
        return new Missy(this);
    }
}

class MissyReturnEffect extends OneShotEffect {

    MissyReturnEffect() {
        super(Outcome.PutCreatureInPlay);
        staticText = "return it to the battlefield under your control face down and tapped. It's a 2/2 Cyberman artifact creature";
    }

    private MissyReturnEffect(final MissyReturnEffect effect) {
        super(effect);
    }

    @Override
    public MissyReturnEffect copy() {
        return new MissyReturnEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Card card = game.getCard(getTargetPointer().getFirst(game, source));
        // a token that died is not a card: nothing to return
        if (controller == null || card == null || game.getState().getZone(card.getId()) != Zone.GRAVEYARD) {
            return false;
        }
        return !CybermanFaceDown.putOntoBattlefield(game, source, controller, Collections.singleton(card), true).isEmpty();
    }
}

class MissyFirstChoice extends VillainousChoice {

    static final FilterControlledPermanent filter = new FilterControlledPermanent("artifact creature you control");

    static {
        filter.add(CardType.ARTIFACT.getPredicate());
        filter.add(CardType.CREATURE.getPredicate());
    }

    MissyFirstChoice() {
        super("Each artifact creature you control deals 1 damage to that opponent",
                "Each artifact creature {controller} controls deals 1 damage to you");
    }

    @Override
    public boolean doChoice(Player player, Game game, Ability source) {
        boolean damaged = false;
        for (Permanent permanent : game.getBattlefield().getActivePermanents(
                MissyFirstChoice.filter, source.getControllerId(), source, game
        )) {
            damaged |= player.damage(1, permanent.getId(), source, game) > 0;
        }
        return damaged;
    }
}

class MissySecondChoice extends VillainousChoice {

    MissySecondChoice() {
        super("you draw a card and chaos ensues", "{controller} draws a card and chaos ensues");
    }

    @Override
    public boolean doChoice(Player player, Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        // "chaos ensues" does nothing without a planar deck, and XMage has no planes
        return controller != null && controller.drawCards(1, source, game) > 0;
    }
}
