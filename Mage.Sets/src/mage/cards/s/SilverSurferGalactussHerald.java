package mage.cards.s;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.DealsCombatDamageToAPlayerTriggeredAbility;
import mage.abilities.common.EntersBattlefieldTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.RequirementEffect;
import mage.abilities.effects.common.search.SearchLibraryPutInHandEffect;
import mage.abilities.keyword.FlyingAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.filter.FilterCard;
import mage.filter.predicate.mageobject.NamePredicate;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.target.common.TargetCardInLibrary;
import mage.target.common.TargetCreaturePermanent;
import mage.target.targetpointer.FixedTarget;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class SilverSurferGalactussHerald extends CardImpl {

    private static final FilterCard filter = new FilterCard("a card named Galactus, Devourer of Worlds");

    static {
        filter.add(new NamePredicate("Galactus, Devourer of Worlds"));
    }

    public SilverSurferGalactussHerald(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{5}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.ALIEN);
        this.subtype.add(SubType.HERO);
        this.power = new MageInt(4);
        this.toughness = new MageInt(5);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // When Silver Surfer enters, you may search your library for a card named Galactus, Devourer of Worlds, reveal it, put it into your hand, then shuffle.
        this.addAbility(new EntersBattlefieldTriggeredAbility(
                new SearchLibraryPutInHandEffect(new TargetCardInLibrary(filter), true), true
        ));

        // Whenever Silver Surfer deals combat damage to a player, until the end of your next turn, target creature attacks that player each combat if able.
        Ability ability = new DealsCombatDamageToAPlayerTriggeredAbility(new SilverSurferGalactussHeraldEffect());
        ability.addTarget(new TargetCreaturePermanent());
        this.addAbility(ability);
    }

    private SilverSurferGalactussHerald(final SilverSurferGalactussHerald card) {
        super(card);
    }

    @Override
    public SilverSurferGalactussHerald copy() {
        return new SilverSurferGalactussHerald(this);
    }
}

class SilverSurferGalactussHeraldEffect extends OneShotEffect {

    SilverSurferGalactussHeraldEffect() {
        super(Outcome.Detriment);
        staticText = "until the end of your next turn, target creature attacks that player each combat if able";
    }

    private SilverSurferGalactussHeraldEffect(final SilverSurferGalactussHeraldEffect effect) {
        super(effect);
    }

    @Override
    public SilverSurferGalactussHeraldEffect copy() {
        return new SilverSurferGalactussHeraldEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        UUID playerId = (UUID) getValue("damagedPlayer");
        Permanent creature = game.getPermanent(getTargetPointer().getFirst(game, source));
        if (playerId == null || creature == null) {
            return false;
        }
        game.addEffect(new SilverSurferGalactussHeraldRequirementEffect(playerId)
                .setTargetPointer(new FixedTarget(creature, game)), source);
        return true;
    }
}

class SilverSurferGalactussHeraldRequirementEffect extends RequirementEffect {

    private final UUID playerId;

    SilverSurferGalactussHeraldRequirementEffect(UUID playerId) {
        super(Duration.UntilEndOfYourNextTurn);
        this.playerId = playerId;
    }

    private SilverSurferGalactussHeraldRequirementEffect(final SilverSurferGalactussHeraldRequirementEffect effect) {
        super(effect);
        this.playerId = effect.playerId;
    }

    @Override
    public SilverSurferGalactussHeraldRequirementEffect copy() {
        return new SilverSurferGalactussHeraldRequirementEffect(this);
    }

    @Override
    public boolean applies(Permanent permanent, Ability source, Game game) {
        if (getTargetPointer().getFirst(game, source) == null) {
            discard();
            return false;
        }
        return permanent.getId().equals(getTargetPointer().getFirst(game, source));
    }

    @Override
    public boolean mustAttack(Game game) {
        return true;
    }

    @Override
    public boolean mustBlock(Game game) {
        return false;
    }

    @Override
    public UUID mustAttackDefender(Ability source, Game game) {
        return playerId;
    }
}
