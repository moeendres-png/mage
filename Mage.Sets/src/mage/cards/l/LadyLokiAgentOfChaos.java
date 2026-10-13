package mage.cards.l;

import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.common.SpellCastControllerTriggeredAbility;
import mage.abilities.effects.OneShotEffect;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.*;
import mage.filter.FilterSpell;
import mage.filter.predicate.Predicates;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.stack.Spell;
import mage.game.stack.StackObject;
import mage.players.Player;
import mage.util.CardUtil;
import mage.watchers.Watcher;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * @author commander-lab
 */
public final class LadyLokiAgentOfChaos extends CardImpl {

    private static final FilterSpell filter
            = new FilterSpell("your first instant, sorcery, or Villain spell each turn");

    static {
        filter.add(Predicates.or(
                CardType.INSTANT.getPredicate(),
                CardType.SORCERY.getPredicate(),
                SubType.VILLAIN.getPredicate()
        ));
        filter.add(LadyLokiAgentOfChaosWatcher::checkSpell);
    }

    public LadyLokiAgentOfChaos(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{5}{R}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.GOD);
        this.subtype.add(SubType.SORCERER);
        this.subtype.add(SubType.VILLAIN);
        this.power = new MageInt(5);
        this.toughness = new MageInt(5);

        // Whenever you cast your first instant, sorcery, or Villain spell each turn, exile it, then exile cards from the top of your library until you exile a nonland card. Lady Loki deals damage to each opponent equal to the difference between that spell's mana value and that nonland card's mana value. You may cast that card without paying its mana cost.
        this.addAbility(new SpellCastControllerTriggeredAbility(
                new LadyLokiAgentOfChaosEffect(), filter, false
        ), new LadyLokiAgentOfChaosWatcher());
    }

    private LadyLokiAgentOfChaos(final LadyLokiAgentOfChaos card) {
        super(card);
    }

    @Override
    public LadyLokiAgentOfChaos copy() {
        return new LadyLokiAgentOfChaos(this);
    }
}

class LadyLokiAgentOfChaosEffect extends OneShotEffect {

    LadyLokiAgentOfChaosEffect() {
        super(Outcome.Benefit);
        staticText = "exile it, then exile cards from the top of your library until you exile a nonland card. "
                + "{this} deals damage to each opponent equal to the difference between that spell's mana value "
                + "and that nonland card's mana value. You may cast that card without paying its mana cost";
    }

    private LadyLokiAgentOfChaosEffect(final LadyLokiAgentOfChaosEffect effect) {
        super(effect);
    }

    @Override
    public LadyLokiAgentOfChaosEffect copy() {
        return new LadyLokiAgentOfChaosEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Spell spell = (Spell) getValue("spellCast");
        if (controller == null || spell == null) {
            return false;
        }
        int spellManaValue = spell.getManaValue();
        Spell onStack = game.getSpell(spell.getId());
        if (onStack != null && !onStack.isCopy()) {
            controller.moveCards(onStack.getMainCard(), Zone.EXILED, source, game);
        }
        Card nonland = null;
        Cards exiled = new CardsImpl();
        for (Card card : controller.getLibrary().getCards(game)) {
            exiled.add(card);
            if (!card.isLand(game)) {
                nonland = card;
                break;
            }
        }
        controller.moveCards(exiled, Zone.EXILED, source, game);
        if (nonland == null) {
            return true;
        }
        int amount = Math.abs(spellManaValue - nonland.getManaValue());
        if (amount > 0) {
            for (UUID opponentId : game.getOpponents(source.getControllerId())) {
                Player opponent = game.getPlayer(opponentId);
                if (opponent != null) {
                    opponent.damage(amount, source.getSourceId(), source, game);
                }
            }
        }
        if (game.getState().getZone(nonland.getId()) == Zone.EXILED) {
            CardUtil.castSpellWithAttributesForFree(controller, source, game, nonland);
        }
        return true;
    }
}

class LadyLokiAgentOfChaosWatcher extends Watcher {

    private final Map<UUID, Integer> playerMap = new HashMap<>();

    LadyLokiAgentOfChaosWatcher() {
        super(WatcherScope.GAME);
    }

    @Override
    public void watch(GameEvent event, Game game) {
        if (event.getType() != GameEvent.EventType.SPELL_CAST) {
            return;
        }
        Spell spell = game.getSpell(event.getTargetId());
        if (spell != null && (spell.isInstantOrSorcery(game) || spell.hasSubtype(SubType.VILLAIN, game))) {
            playerMap.compute(spell.getControllerId(), CardUtil::setOrIncrementValue);
        }
    }

    @Override
    public void reset() {
        super.reset();
        playerMap.clear();
    }

    static boolean checkSpell(StackObject input, Game game) {
        return game
                .getState()
                .getWatcher(LadyLokiAgentOfChaosWatcher.class).playerMap
                .getOrDefault(input.getControllerId(), 0) < 2;
    }
}
