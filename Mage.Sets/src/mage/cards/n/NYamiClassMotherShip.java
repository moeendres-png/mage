package mage.cards.n;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.DealsCombatDamageToAPlayerTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.keyword.CrewAbility;
import mage.abilities.keyword.FlyingAbility;
import mage.abilities.keyword.HasteAbility;
import mage.abilities.keyword.VigilanceAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.CardsImpl;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.Zone;
import mage.game.Game;
import mage.players.Player;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class NYamiClassMotherShip extends CardImpl {

    public NYamiClassMotherShip(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT}, "{6}");

        this.subtype.add(SubType.VEHICLE);
        this.power = new MageInt(5);
        this.toughness = new MageInt(7);

        // Flying, vigilance, haste
        this.addAbility(FlyingAbility.getInstance());
        this.addAbility(VigilanceAbility.getInstance());
        this.addAbility(HasteAbility.getInstance());

        // Whenever this Vehicle deals combat damage to a player, look at the top card of your library. If it's a permanent card, you may put it onto the battlefield. If you don't put it onto the battlefield, put it into your hand.
        this.addAbility(new DealsCombatDamageToAPlayerTriggeredAbility(new NYamiClassMotherShipEffect()));

        // Crew 3
        this.addAbility(new CrewAbility(3));
    }

    private NYamiClassMotherShip(final NYamiClassMotherShip card) {
        super(card);
    }

    @Override
    public NYamiClassMotherShip copy() {
        return new NYamiClassMotherShip(this);
    }
}

class NYamiClassMotherShipEffect extends OneShotEffect {

    NYamiClassMotherShipEffect() {
        super(Outcome.PutCardInPlay);
        staticText = "look at the top card of your library. If it's a permanent card, you may put it onto the "
                + "battlefield. If you don't put it onto the battlefield, put it into your hand";
    }

    private NYamiClassMotherShipEffect(final NYamiClassMotherShipEffect effect) {
        super(effect);
    }

    @Override
    public NYamiClassMotherShipEffect copy() {
        return new NYamiClassMotherShipEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        Card card = controller.getLibrary().getFromTop(game);
        if (card == null) {
            return false;
        }
        controller.lookAtCards(source, null, new CardsImpl(card), game);
        if (card.isPermanent(game)
                && controller.chooseUse(Outcome.PutCardInPlay, "Put " + card.getName() + " onto the battlefield?", source, game)
                && controller.moveCards(card, Zone.BATTLEFIELD, source, game)) {
            return true;
        }
        return controller.moveCards(card, Zone.HAND, source, game);
    }
}
