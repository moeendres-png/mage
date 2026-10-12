package mage.cards.d;

import mage.MageIdentifier;
import mage.MageInt;
import mage.MageObject;
import mage.abilities.Ability;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.costs.Cost;
import mage.abilities.costs.Costs;
import mage.abilities.costs.CostsImpl;
import mage.abilities.costs.common.DiscardCardCost;
import mage.abilities.dynamicvalue.DynamicValue;
import mage.abilities.effects.AsThoughEffectImpl;
import mage.abilities.effects.Effect;
import mage.abilities.effects.common.continuous.SetBasePowerSourceEffect;
import mage.abilities.keyword.FlyingAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.AsThoughEffectType;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.Zone;
import mage.filter.StaticFilters;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.players.Player;

import java.util.UUID;

/**
 * @author commander-lab
 */
public final class DragonManReformedRobot extends CardImpl {

    public DragonManReformedRobot(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ARTIFACT, CardType.CREATURE}, "{2}{W}{U}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.DRAGON);
        this.subtype.add(SubType.ROBOT);
        this.power = new MageInt(0);
        this.toughness = new MageInt(5);

        // Flying
        this.addAbility(FlyingAbility.getInstance());

        // Dragon Man's power is equal to the greatest mana value among noncreature permanents you control and noncreature cards in your graveyard.
        this.addAbility(new SimpleStaticAbility(Zone.ALL, new SetBasePowerSourceEffect(DragonManReformedRobotValue.instance)));

        // You may cast this card from your graveyard by discarding a card in addition to paying its other costs.
        this.addAbility(new SimpleStaticAbility(Zone.GRAVEYARD, new DragonManReformedRobotGraveyardEffect())
                .setIdentifier(MageIdentifier.DragonManReformedRobotAlternateCast));
    }

    private DragonManReformedRobot(final DragonManReformedRobot card) {
        super(card);
    }

    @Override
    public DragonManReformedRobot copy() {
        return new DragonManReformedRobot(this);
    }
}

enum DragonManReformedRobotValue implements DynamicValue {
    instance;

    @Override
    public int calculate(Game game, Ability sourceAbility, Effect effect) {
        int greatest = 0;
        for (Permanent permanent : game.getBattlefield().getActivePermanents(
                StaticFilters.FILTER_CONTROLLED_PERMANENT, sourceAbility.getControllerId(), sourceAbility, game)) {
            if (!permanent.isCreature(game)) {
                greatest = Math.max(greatest, permanent.getManaValue());
            }
        }
        Player controller = game.getPlayer(sourceAbility.getControllerId());
        if (controller != null) {
            for (Card card : controller.getGraveyard().getCards(game)) {
                if (!card.isCreature(game)) {
                    greatest = Math.max(greatest, card.getManaValue());
                }
            }
        }
        return greatest;
    }

    @Override
    public DragonManReformedRobotValue copy() {
        return this;
    }

    @Override
    public String getMessage() {
        return "the greatest mana value among noncreature permanents you control and noncreature cards in your graveyard";
    }

    @Override
    public String toString() {
        return "1";
    }
}

class DragonManReformedRobotGraveyardEffect extends AsThoughEffectImpl {

    DragonManReformedRobotGraveyardEffect() {
        super(AsThoughEffectType.CAST_FROM_NOT_OWN_HAND_ZONE, Duration.EndOfGame, Outcome.PutCreatureInPlay);
        this.staticText = "You may cast this card from your graveyard by discarding a card in addition to paying its other costs.";
    }

    private DragonManReformedRobotGraveyardEffect(final DragonManReformedRobotGraveyardEffect effect) {
        super(effect);
    }

    @Override
    public DragonManReformedRobotGraveyardEffect copy() {
        return new DragonManReformedRobotGraveyardEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        return true;
    }

    @Override
    public boolean applies(UUID objectId, Ability source, UUID affectedControllerId, Game game) {
        if (!objectId.equals(source.getSourceId()) || !source.isControlledBy(affectedControllerId)
                || game.getState().getZone(source.getSourceId()) != Zone.GRAVEYARD) {
            return false;
        }
        Player controller = game.getPlayer(affectedControllerId);
        MageObject sourceObject = game.getObject(source.getSourceId());
        if (controller == null || sourceObject == null) {
            return false;
        }
        Costs<Cost> costs = new CostsImpl<>();
        costs.add(new DiscardCardCost());
        controller.setCastSourceIdWithAlternateMana(objectId, sourceObject.getManaCost().copy(), costs,
                MageIdentifier.DragonManReformedRobotAlternateCast);
        return true;
    }
}
