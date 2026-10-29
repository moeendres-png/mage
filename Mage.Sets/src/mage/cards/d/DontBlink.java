package mage.cards.d;

import mage.abilities.Ability;
import mage.abilities.costs.mana.ManaCostsImpl;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.ReplacementEffectImpl;
import mage.abilities.keyword.CyclingAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.events.ZoneChangeEvent;
import mage.game.stack.Spell;
import mage.players.Player;

import java.util.UUID;

/**
 * Don't Blink {1}{U}
 * Instant
 * Until end of turn, if one or more creatures would enter from exile or after being cast from exile,
 * their owners shuffle them into their libraries instead.
 * Cycling {2}
 */
public final class DontBlink extends CardImpl {

    public DontBlink(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.INSTANT}, "{1}{U}");

        // Until end of turn, if one or more creatures would enter from exile or after being cast from exile,
        // their owners shuffle them into their libraries instead.
        this.getSpellAbility().addEffect(new DontBlinkEffect());

        // Cycling {2}
        this.addAbility(new CyclingAbility(new ManaCostsImpl<>("{2}")));
    }

    private DontBlink(final DontBlink card) {
        super(card);
    }

    @Override
    public DontBlink copy() {
        return new DontBlink(this);
    }
}

class DontBlinkEffect extends OneShotEffect {

    DontBlinkEffect() {
        super(Outcome.Benefit);
        staticText = "until end of turn, if one or more creatures would enter from exile or after being cast from exile, "
                + "their owners shuffle them into their libraries instead";
    }

    private DontBlinkEffect(final DontBlinkEffect effect) {
        super(effect);
    }

    @Override
    public DontBlinkEffect copy() {
        return new DontBlinkEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        game.addEffect(new DontBlinkReplacementEffect(), source);
        return true;
    }
}

class DontBlinkReplacementEffect extends ReplacementEffectImpl {

    DontBlinkReplacementEffect() {
        super(Duration.EndOfTurn, Outcome.Exile);
        staticText = "if one or more creatures would enter from exile or after being cast from exile, "
                + "their owners shuffle them into their libraries instead";
    }

    private DontBlinkReplacementEffect(final DontBlinkReplacementEffect effect) {
        super(effect);
    }

    @Override
    public DontBlinkReplacementEffect copy() {
        return new DontBlinkReplacementEffect(this);
    }

    @Override
    public boolean checksEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.ZONE_CHANGE;
    }

    @Override
    public boolean applies(GameEvent event, Ability source, Game game) {
        ZoneChangeEvent zEvent = (ZoneChangeEvent) event;
        if (zEvent.getToZone() != Zone.BATTLEFIELD) {
            return false;
        }
        boolean fromExile = zEvent.getFromZone() == Zone.EXILED;
        if (!fromExile && zEvent.getFromZone() == Zone.STACK) {
            // a creature spell that was cast from exile, resolving
            Spell spell = game.getSpellOrLKIStack(event.getSourceId());
            fromExile = spell != null && spell.getFromZone() == Zone.EXILED;
        }
        if (!fromExile) {
            return false;
        }
        Card card = game.getCard(event.getTargetId());
        return card != null && card.isCreature(game);
    }

    @Override
    public boolean replaceEvent(GameEvent event, Ability source, Game game) {
        Card card = game.getCard(event.getTargetId());
        if (card == null) {
            return false;
        }
        Player owner = game.getPlayer(card.getOwnerId());
        if (owner == null) {
            return false;
        }
        owner.shuffleCardsToLibrary(card, game, source);
        return true;
    }
}
