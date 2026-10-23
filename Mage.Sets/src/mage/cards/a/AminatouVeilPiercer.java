package mage.cards.a;

import mage.ApprovingObject;
import mage.MageInt;
import mage.abilities.Ability;
import mage.abilities.SpellAbility;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.costs.mana.ManaCost;
import mage.abilities.costs.mana.ManaCosts;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.keyword.SurveilEffect;
import mage.abilities.keyword.MiracleAbility;
import mage.abilities.triggers.BeginningOfUpkeepTriggeredAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.cards.Cards;
import mage.cards.CardsImpl;
import mage.constants.CardType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.SuperType;
import mage.constants.TargetController;
import mage.constants.WatcherScope;
import mage.constants.Zone;
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
 * @author Claude
 */
public final class AminatouVeilPiercer extends CardImpl {

    public AminatouVeilPiercer(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.CREATURE}, "{1}{W}{U}{B}");

        this.supertype.add(SuperType.LEGENDARY);
        this.subtype.add(SubType.HUMAN);
        this.subtype.add(SubType.WIZARD);
        this.power = new MageInt(2);
        this.toughness = new MageInt(4);

        // At the beginning of your upkeep, surveil 2.
        this.addAbility(new BeginningOfUpkeepTriggeredAbility(TargetController.YOU, new SurveilEffect(2), false));

        // Each enchantment card in your hand has miracle. Its miracle cost is equal to its mana cost reduced by {4}.
        // The standard miracle watcher only looks at abilities a card already has when it is drawn, which is too
        // early for a granted ability. So the miracle is modelled as a trigger on the first draw of the turn.
        this.addAbility(new AminatouVeilPiercerTriggeredAbility(), new AminatouDrawWatcher());
    }

    private AminatouVeilPiercer(final AminatouVeilPiercer card) {
        super(card);
    }

    @Override
    public AminatouVeilPiercer copy() {
        return new AminatouVeilPiercer(this);
    }
}

class AminatouVeilPiercerTriggeredAbility extends TriggeredAbilityImpl {

    AminatouVeilPiercerTriggeredAbility() {
        super(Zone.BATTLEFIELD, new AminatouVeilPiercerEffect(), false);
        setTriggerPhrase("When you draw an enchantment card as the first card you drew this turn, ");
    }

    private AminatouVeilPiercerTriggeredAbility(final AminatouVeilPiercerTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public AminatouVeilPiercerTriggeredAbility copy() {
        return new AminatouVeilPiercerTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DREW_CARD;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!isControlledBy(event.getPlayerId()) || game.getPhase() == null) {
            return false;
        }
        AminatouDrawWatcher watcher = game.getState().getWatcher(AminatouDrawWatcher.class);
        Card card = game.getCard(event.getTargetId());
        if (watcher == null || card == null || watcher.getCardsDrawnThisTurn(event.getPlayerId()) != 1
                || !card.isEnchantment(game) || game.getState().getZone(card.getId()) != Zone.HAND) {
            return false;
        }
        for (Ability ability : card.getAbilities(game)) {
            if (ability instanceof MiracleAbility) {
                return false; // the card has miracle on its own and the standard watcher takes care of it
            }
        }
        getEffects().setTargetPointer(new FixedTarget(card, game));
        return true;
    }

    @Override
    public String getRule() {
        return "Each enchantment card in your hand has miracle. Its miracle cost is equal to its mana cost reduced by {4}.";
    }
}

class AminatouVeilPiercerEffect extends OneShotEffect {

    AminatouVeilPiercerEffect() {
        super(Outcome.Benefit);
        staticText = "you may reveal it and cast it for its miracle cost, which is its mana cost reduced by {4}";
    }

    private AminatouVeilPiercerEffect(final AminatouVeilPiercerEffect effect) {
        super(effect);
    }

    @Override
    public AminatouVeilPiercerEffect copy() {
        return new AminatouVeilPiercerEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        Card card = game.getCard(getTargetPointer().getFirst(game, source));
        if (controller == null || card == null || game.getState().getZone(card.getId()) != Zone.HAND) {
            return false;
        }
        Cards cards = new CardsImpl(card);
        controller.lookAtCards("Miracle", cards, game);
        if (!controller.chooseUse(Outcome.Benefit,
                "Reveal " + card.getLogName() + " and cast it for its miracle cost?", source, game)) {
            return false;
        }
        controller.revealCards("Miracle", cards, game);
        SpellAbility abilityToCast = card.getSpellAbility().copy();
        ManaCosts<ManaCost> reduced = CardUtil.reduceCost(card.getSpellAbility().getManaCostsToPay(), 4);
        ManaCosts<ManaCost> costRef = abilityToCast.getManaCostsToPay();
        costRef.clear();
        costRef.add(reduced);
        return controller.cast(abilityToCast, game, false, new ApprovingObject(source, game));
    }
}

/**
 * Counts the cards each player drew this turn.
 */
class AminatouDrawWatcher extends Watcher {

    private final Map<UUID, Integer> cardsDrawnThisTurn = new HashMap<>();

    AminatouDrawWatcher() {
        super(WatcherScope.GAME);
    }

    @Override
    public void watch(GameEvent event, Game game) {
        if (event.getType() == GameEvent.EventType.UNTAP_STEP_PRE) {
            reset();
        }
        if (event.getType() == GameEvent.EventType.DREW_CARD && event.getPlayerId() != null) {
            cardsDrawnThisTurn.merge(event.getPlayerId(), 1, Integer::sum);
        }
    }

    int getCardsDrawnThisTurn(UUID playerId) {
        return cardsDrawnThisTurn.getOrDefault(playerId, 0);
    }

    @Override
    public void reset() {
        super.reset();
        cardsDrawnThisTurn.clear();
    }
}
