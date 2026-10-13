package mage.cards.m;

import mage.ApprovingObject;
import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.SpellAbility;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.costs.mana.ManaCostsImpl;
import mage.abilities.effects.OneShotEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.CardsImpl;
import mage.constants.*;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.players.Player;
import mage.target.targetpointer.FixedTarget;
import mage.util.CardUtil;
import mage.watchers.Watcher;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Nonland cards in your hand have miracle {0}. Modeled as the miracle trigger itself:
 * when you draw your first card of a turn and it is a nonland card still in your hand,
 * you may reveal it; on resolution you may cast it for {0} (rule 702.94a).
 *
 * @author commander-lab
 */
public final class MoleculeMan extends CardImpl {

    public MoleculeMan(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{6}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.VILLAIN);
        this.power = new MageInt(5);
        this.toughness = new MageInt(5);

        // Nonland cards in your hand have miracle {0}.
        this.addAbility(new MoleculeManMiracleTriggeredAbility(), new MoleculeManDrawWatcher());
    }

    private MoleculeMan(final MoleculeMan card) {
        super(card);
    }

    @Override
    public MoleculeMan copy() {
        return new MoleculeMan(this);
    }
}

class MoleculeManMiracleTriggeredAbility extends TriggeredAbilityImpl {

    MoleculeManMiracleTriggeredAbility() {
        super(Zone.BATTLEFIELD, new MoleculeManCastEffect(), true);
    }

    private MoleculeManMiracleTriggeredAbility(final MoleculeManMiracleTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public MoleculeManMiracleTriggeredAbility copy() {
        return new MoleculeManMiracleTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DREW_CARD;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!isControlledBy(event.getPlayerId()) || game.getPhase() == null
                || !MoleculeManDrawWatcher.isFirstDraw(event.getPlayerId(), game)) {
            return false;
        }
        Card card = game.getCard(event.getTargetId());
        if (card == null || card.isLand(game) || game.getState().getZone(card.getId()) != Zone.HAND) {
            return false;
        }
        getEffects().setTargetPointer(new FixedTarget(card, game));
        return true;
    }

    @Override
    public boolean resolve(Game game) {
        Player controller = game.getPlayer(getControllerId());
        Card card = game.getCard(getEffects().get(0).getTargetPointer().getFirst(game, this));
        if (controller != null && card != null) {
            controller.revealCards("Miracle", new CardsImpl(card), game);
        }
        return super.resolve(game);
    }

    @Override
    public String getRule() {
        return "Nonland cards in your hand have miracle {0}. <i>(You may cast a card for its miracle cost "
                + "when you draw it if it's the first card you drew this turn.)</i>";
    }
}

class MoleculeManCastEffect extends OneShotEffect {

    MoleculeManCastEffect() {
        super(Outcome.PlayForFree);
        staticText = "cast that card for its miracle cost {0}";
    }

    private MoleculeManCastEffect(final MoleculeManCastEffect effect) {
        super(effect);
    }

    @Override
    public MoleculeManCastEffect copy() {
        return new MoleculeManCastEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Card card = game.getCard(getTargetPointer().getFirst(game, source));
        if (controller == null || card == null || game.getState().getZone(card.getId()) != Zone.HAND) {
            return false;
        }
        if (!controller.chooseUse(Outcome.PlayForFree, "Cast " + card.getLogName() + " for its miracle cost {0}?", source, game)) {
            return false;
        }
        SpellAbility abilityToCast = card.getSpellAbility().copy();
        abilityToCast.getManaCostsToPay().clear();
        abilityToCast.getManaCostsToPay().add(new ManaCostsImpl<>("{0}"));
        controller.cast(abilityToCast, game, false, new ApprovingObject(source, game));
        return true;
    }
}

class MoleculeManDrawWatcher extends Watcher {

    private final Map<UUID, Integer> drawn = new HashMap<>();

    MoleculeManDrawWatcher() {
        super(WatcherScope.GAME);
    }

    @Override
    public void watch(GameEvent event, Game game) {
        if (event.getType() == GameEvent.EventType.DREW_CARD && game.getPhase() != null && event.getPlayerId() != null) {
            drawn.compute(event.getPlayerId(), CardUtil::setOrIncrementValue);
        }
    }

    @Override
    public void reset() {
        super.reset();
        drawn.clear();
    }

    static boolean isFirstDraw(UUID playerId, Game game) {
        MoleculeManDrawWatcher watcher = game.getState().getWatcher(MoleculeManDrawWatcher.class);
        return watcher != null && watcher.drawn.getOrDefault(playerId, 0) == 1;
    }
}
