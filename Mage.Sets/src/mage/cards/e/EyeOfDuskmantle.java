package mage.cards.e;

import mage.MageIdentifier;
import mage.MageInt;
import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.common.SimpleStaticAbility;
import mage.abilities.costs.Costs;
import mage.abilities.costs.CostsImpl;
import mage.abilities.costs.common.PayLifeCost;
import mage.abilities.effects.AsThoughEffectImpl;
import mage.abilities.keyword.FlyingAbility;
import mage.abilities.keyword.LifelinkAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.AsThoughEffectType;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.WatcherScope;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.players.Player;
import mage.watchers.Watcher;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * Eye of Duskmantle {5}{B}{B}
 * Creature -- Eye 3/8
 * Flying, lifelink
 * You may play lands and cast spells from among cards in your graveyard you've surveilled this turn.
 * If you cast a spell this way, you pay life equal to its mana value rather than paying its mana cost.
 */
public final class EyeOfDuskmantle extends CardImpl {

    public EyeOfDuskmantle(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{5}{B}{B}");

        this.subtype.add(SubType.EYE);
        this.power = new MageInt(3);
        this.toughness = new MageInt(8);

        // Flying, lifelink
        this.addAbility(FlyingAbility.getInstance());
        this.addAbility(LifelinkAbility.getInstance());

        // You may play lands and cast spells from among cards in your graveyard you've surveilled this turn.
        // If you cast a spell this way, you pay life equal to its mana value rather than paying its mana cost.
        this.addAbility(new SimpleStaticAbility(new EyeOfDuskmantlePlayEffect())
                .setIdentifier(MageIdentifier.EyeOfDuskmantleAlternateCast), new EyeOfDuskmantleWatcher());
    }

    private EyeOfDuskmantle(final EyeOfDuskmantle card) {
        super(card);
    }

    @Override
    public EyeOfDuskmantle copy() {
        return new EyeOfDuskmantle(this);
    }
}

class EyeOfDuskmantlePlayEffect extends AsThoughEffectImpl {

    EyeOfDuskmantlePlayEffect() {
        super(AsThoughEffectType.PLAY_FROM_NOT_OWN_HAND_ZONE, Duration.WhileOnBattlefield, Outcome.Benefit);
        staticText = "You may play lands and cast spells from among cards in your graveyard you've surveilled this turn. "
                + "If you cast a spell this way, you pay life equal to its mana value rather than paying its mana cost";
    }

    private EyeOfDuskmantlePlayEffect(final EyeOfDuskmantlePlayEffect effect) {
        super(effect);
    }

    @Override
    public EyeOfDuskmantlePlayEffect copy() {
        return new EyeOfDuskmantlePlayEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        return true;
    }

    @Override
    public boolean applies(UUID objectId, Ability source, UUID affectedControllerId, Game game) {
        if (!affectedControllerId.equals(source.getControllerId())) {
            return false;
        }
        Card cardToCheck = game.getCard(objectId);
        if (cardToCheck == null) {
            return false;
        }
        Card mainCard = cardToCheck.getMainCard();
        Player player = game.getPlayer(affectedControllerId);
        if (player == null
                || !mainCard.isOwnedBy(affectedControllerId)
                || game.getState().getZone(mainCard.getId()) != Zone.GRAVEYARD
                || !player.getGraveyard().contains(mainCard.getId())) {
            return false;
        }
        EyeOfDuskmantleWatcher watcher = game.getState().getWatcher(EyeOfDuskmantleWatcher.class);
        if (watcher == null || !watcher.wasSurveilledThisTurn(affectedControllerId, mainCard, game)) {
            return false;
        }
        // spells are paid with life equal to their mana value instead of their mana cost
        if (!cardToCheck.isLand(game)) {
            Costs newCosts = new CostsImpl();
            newCosts.add(new PayLifeCost(cardToCheck.getSpellAbility().getManaCosts().manaValue()));
            newCosts.addAll(cardToCheck.getSpellAbility().getCosts());
            player.setCastSourceIdWithAlternateMana(cardToCheck.getId(), null, newCosts, MageIdentifier.EyeOfDuskmantleAlternateCast);
        }
        return true;
    }
}

class EyeOfDuskmantleWatcher extends Watcher {

    private final Map<UUID, Set<MageObjectReference>> surveilled = new HashMap<>();

    EyeOfDuskmantleWatcher() {
        super(WatcherScope.GAME);
    }

    @Override
    public void watch(GameEvent event, Game game) {
        if (event.getType() != GameEvent.EventType.SURVEILED_INTO_GRAVEYARD) {
            return;
        }
        surveilled.computeIfAbsent(event.getPlayerId(), x -> new HashSet<>())
                .add(new MageObjectReference(event.getTargetId(), game));
    }

    boolean wasSurveilledThisTurn(UUID playerId, Card card, Game game) {
        return surveilled.getOrDefault(playerId, new HashSet<>()).stream().anyMatch(mor -> mor.refersTo(card, game));
    }

    @Override
    public void reset() {
        super.reset();
        surveilled.clear();
    }
}
