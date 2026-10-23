package mage.cards.j;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.EntersBattlefieldOrAttacksSourceTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.common.TargetOpponent;

import java.util.UUID;

/**
 * @author Claude
 */
public final class JhoiraWeatherlightCorsair extends CardImpl {

    public JhoiraWeatherlightCorsair(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{4}{B}{B}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.PIRATE);
        this.power = new MageInt(4);
        this.toughness = new MageInt(5);

        // Whenever Jhoira enters or attacks, target opponent reveals cards from the top of their library until
        // they reveal a historic permanent card. You put that card onto the battlefield under your control and lose
        // life equal to that permanent's mana value. That player puts the rest of the revealed cards on the bottom
        // of their library in a random order.
        Ability ability = new EntersBattlefieldOrAttacksSourceTriggeredAbility(new JhoiraWeatherlightCorsairEffect());
        ability.addTarget(new TargetOpponent());
        this.addAbility(ability);
    }

    private JhoiraWeatherlightCorsair(final JhoiraWeatherlightCorsair card) {
        super(card);
    }

    @Override
    public JhoiraWeatherlightCorsair copy() {
        return new JhoiraWeatherlightCorsair(this);
    }
}

class JhoiraWeatherlightCorsairEffect extends OneShotEffect {

    JhoiraWeatherlightCorsairEffect() {
        super(Outcome.PutCardInPlay);
        staticText = "target opponent reveals cards from the top of their library until they reveal a historic "
                + "permanent card. You put that card onto the battlefield under your control and lose life equal to "
                + "that permanent's mana value. That player puts the rest of the revealed cards on the bottom of "
                + "their library in a random order. <i>(Artifacts, legendaries, and Sagas are historic.)</i>";
    }

    private JhoiraWeatherlightCorsairEffect(final JhoiraWeatherlightCorsairEffect effect) {
        super(effect);
    }

    @Override
    public JhoiraWeatherlightCorsairEffect copy() {
        return new JhoiraWeatherlightCorsairEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Player opponent = game.getPlayer(getTargetPointer().getFirst(game, source));
        if (controller == null || opponent == null) {
            return false;
        }
        Cards revealed = new CardsImpl();
        Card found = null;
        for (Card card : opponent.getLibrary().getCards(game)) {
            revealed.add(card);
            if (card.isPermanent(game) && card.isHistoric(game)) {
                found = card;
                break;
            }
        }
        opponent.revealCards(source, revealed, game);
        if (found != null) {
            int manaValue = found.getManaValue();
            if (controller.moveCards(found, Zone.BATTLEFIELD, source, game)) {
                game.processAction();
                Permanent permanent = game.getPermanent(found.getId());
                if (permanent != null) {
                    manaValue = permanent.getManaValue();
                }
                controller.loseLife(manaValue, game, source, false);
            }
            revealed.remove(found);
        }
        revealed.retainZone(Zone.LIBRARY, game);
        opponent.putCardsOnBottomOfLibrary(revealed, game, source, false);
        return true;
    }
}
