package mage.cards.c;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.DealsCombatDamageToAPlayerTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.keyword.CybermanFaceDown;
import mage.abilities.keyword.CrewAbility;
import mage.abilities.keyword.FlyingAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.game.Game;
import mage.players.Player;

import java.util.HashSet;
import java.util.Set;
import java.util.UUID;

/**
 * @author Claude
 */
public final class Cybership extends CardImpl {

    public Cybership(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT}, "{6}");

        this.subtype.add(SubType.VEHICLE);
        this.power = new MageInt(8);
        this.toughness = new MageInt(8);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // Whenever this Vehicle deals combat damage to a player, put the top two cards of that player's library onto the battlefield face down under your control. They're 2/2 Cyberman artifact creatures.
        this.addAbility(new DealsCombatDamageToAPlayerTriggeredAbility(new CybershipEffect(), false, true));

        // Crew 4
        this.addAbility(new CrewAbility(4));
    }

    private Cybership(final Cybership card) {
        super(card);
    }

    @Override
    public Cybership copy() {
        return new Cybership(this);
    }
}

class CybershipEffect extends OneShotEffect {

    CybershipEffect() {
        super(Outcome.PutCardInPlay);
        staticText = "put the top two cards of that player's library onto the battlefield face down " +
                "under your control. They're 2/2 Cyberman artifact creatures";
    }

    private CybershipEffect(final CybershipEffect effect) {
        super(effect);
    }

    @Override
    public CybershipEffect copy() {
        return new CybershipEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Player damaged = game.getPlayer(getTargetPointer().getFirst(game, source));
        if (controller == null || damaged == null) {
            return false;
        }
        Set<Card> cards = new HashSet<>(damaged.getLibrary().getTopCards(game, 2));
        return !CybermanFaceDown.putOntoBattlefield(game, source, controller, cards, false).isEmpty();
    }
}
