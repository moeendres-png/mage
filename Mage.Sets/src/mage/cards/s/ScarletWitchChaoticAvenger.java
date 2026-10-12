package mage.cards.s;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.DealsCombatDamageToAPlayerTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.keyword.FlyingAbility;
import mage.cards.Card;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.filter.FilterCard;
import mage.filter.predicate.Predicates;
import mage.game.ExileZone;
import mage.game.Game;
import mage.players.Player;
import mage.util.CardUtil;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class ScarletWitchChaoticAvenger extends CardImpl {

    public ScarletWitchChaoticAvenger(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{2}{U}{R}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.MUTANT);
        this.subtype.add(SubType.WARLOCK);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(3);
        this.toughness = new MageInt(3);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // Whenever Scarlet Witch deals combat damage to a player, look at the top two cards of your library, then exile them face down. Then you may cast a Hero or noncreature spell from among cards exiled with Scarlet Witch without paying its mana cost.
        this.addAbility(new DealsCombatDamageToAPlayerTriggeredAbility(new ScarletWitchChaoticAvengerEffect()));
    }

    private ScarletWitchChaoticAvenger(final ScarletWitchChaoticAvenger card) {
        super(card);
    }

    @Override
    public ScarletWitchChaoticAvenger copy() {
        return new ScarletWitchChaoticAvenger(this);
    }
}

class ScarletWitchChaoticAvengerEffect extends OneShotEffect {

    private static final FilterCard filter = new FilterCard("Hero or noncreature spell");

    static {
        filter.add(Predicates.or(
                SubType.HERO.getPredicate(),
                Predicates.not(CardType.CREATURE.getPredicate())
        ));
    }

    ScarletWitchChaoticAvengerEffect() {
        super(Outcome.PlayForFree);
        staticText = "look at the top two cards of your library, then exile them face down. Then you may cast "
                + "a Hero or noncreature spell from among cards exiled with {this} without paying its mana cost";
    }

    private ScarletWitchChaoticAvengerEffect(final ScarletWitchChaoticAvengerEffect effect) {
        super(effect);
    }

    @Override
    public ScarletWitchChaoticAvengerEffect copy() {
        return new ScarletWitchChaoticAvengerEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        Cards top = new CardsImpl(controller.getLibrary().getTopCards(game, 2));
        UUID exileZoneId = CardUtil.getExileZoneId(game, source);
        if (!top.isEmpty()) {
            controller.lookAtCards(source, null, top, game);
            controller.moveCardsToExile(top.getCards(game), source, game, false, exileZoneId, CardUtil.getSourceName(game, source));
            for (Card card : top.getCards(game)) {
                card.setFaceDown(true, game);
            }
        }
        ExileZone exileZone = game.getExile().getExileZone(exileZoneId);
        if (exileZone == null || exileZone.isEmpty()) {
            return true;
        }
        Cards exiled = new CardsImpl(exileZone.getCards(game));
        CardUtil.castSpellWithAttributesForFree(controller, source, game, exiled, filter);
        return true;
    }
}
