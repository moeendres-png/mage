package mage.cards.d;

import mage.abilities.Ability;
import mage.abilities.DelayedTriggeredAbility;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.common.delayed.AtTheBeginOfNextEndStepDelayedTriggeredAbility;
import mage.abilities.condition.common.PermanentsOnTheBattlefieldCondition;
import mage.abilities.dynamicvalue.common.PermanentsOnBattlefieldCount;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.CreateTokenEffect;
import mage.abilities.effects.common.ReturnToBattlefieldUnderYourControlTargetEffect;
import mage.abilities.keyword.HasteAbility;
import mage.abilities.triggers.BeginningOfCombatTriggeredAbility;
import mage.cards.Card;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.ComparisonType;
import mage.constants.Outcome;
import mage.constants.SubType;
import mage.constants.TargetController;
import mage.constants.Zone;
import mage.filter.FilterPermanent;
import mage.filter.common.FilterControlledPermanent;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.events.ZoneChangeEvent;
import mage.game.permanent.Permanent;
import mage.game.permanent.token.SandWarriorToken;
import mage.target.targetpointer.FixedTarget;

import java.util.UUID;

/**
 * Desert Warfare {3}{G}
 * Enchantment
 * Whenever you sacrifice a Desert and whenever a Desert card is put into your graveyard from your hand or library,
 * put that card onto the battlefield under your control at the beginning of your next end step.
 * At the beginning of combat on your turn, if you control five or more Deserts, create that many 1/1 red, green,
 * and white Sand Warrior creature tokens. They gain haste.
 */
public final class DesertWarfare extends CardImpl {

    private static final FilterPermanent filter = new FilterControlledPermanent(SubType.DESERT, "Deserts");
    private static final PermanentsOnBattlefieldCount xValue = new PermanentsOnBattlefieldCount(filter);

    public DesertWarfare(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ENCHANTMENT}, "{3}{G}");

        // Whenever you sacrifice a Desert and whenever a Desert card is put into your graveyard from your hand or library,
        // put that card onto the battlefield under your control at the beginning of your next end step.
        this.addAbility(new DesertWarfareTriggeredAbility());

        // At the beginning of combat on your turn, if you control five or more Deserts, create that many
        // 1/1 red, green, and white Sand Warrior creature tokens. They gain haste.
        SandWarriorToken token = new SandWarriorToken();
        token.addAbility(HasteAbility.getInstance());
        CreateTokenEffect tokenEffect = new CreateTokenEffect(token, xValue);
        tokenEffect.setText("create that many 1/1 red, green, and white Sand Warrior creature tokens. They gain haste");
        this.addAbility(new BeginningOfCombatTriggeredAbility(
                TargetController.YOU, tokenEffect, false
        ).withInterveningIf(new PermanentsOnTheBattlefieldCondition(filter, ComparisonType.MORE_THAN, 4)));
    }

    private DesertWarfare(final DesertWarfare card) {
        super(card);
    }

    @Override
    public DesertWarfare copy() {
        return new DesertWarfare(this);
    }
}

class DesertWarfareTriggeredAbility extends TriggeredAbilityImpl {

    DesertWarfareTriggeredAbility() {
        super(Zone.BATTLEFIELD, new DesertWarfareEffect(), false);
        setTriggerPhrase("Whenever you sacrifice a Desert and whenever a Desert card is put into your graveyard from your hand or library, ");
    }

    private DesertWarfareTriggeredAbility(final DesertWarfareTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public DesertWarfareTriggeredAbility copy() {
        return new DesertWarfareTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.SACRIFICED_PERMANENT
                || event.getType() == GameEvent.EventType.ZONE_CHANGE;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        Card card;
        if (event.getType() == GameEvent.EventType.SACRIFICED_PERMANENT) {
            if (!isControlledBy(event.getPlayerId())) {
                return false;
            }
            Permanent permanent = game.getPermanentOrLKIBattlefield(event.getTargetId());
            if (permanent == null || !permanent.hasSubtype(SubType.DESERT, game)) {
                return false;
            }
            card = game.getCard(event.getTargetId());
        } else {
            ZoneChangeEvent zEvent = (ZoneChangeEvent) event;
            if (zEvent.getToZone() != Zone.GRAVEYARD
                    || (zEvent.getFromZone() != Zone.HAND && zEvent.getFromZone() != Zone.LIBRARY)) {
                return false;
            }
            card = game.getCard(event.getTargetId());
            if (card == null || !card.isOwnedBy(getControllerId()) || !card.hasSubtype(SubType.DESERT, game)) {
                return false;
            }
        }
        if (card == null) {
            return false; // a sacrificed token is no card
        }
        getEffects().setTargetPointer(new FixedTarget(card, game));
        return true;
    }
}

class DesertWarfareEffect extends OneShotEffect {

    DesertWarfareEffect() {
        super(Outcome.PutCardInPlay);
        staticText = "put that card onto the battlefield under your control at the beginning of your next end step";
    }

    private DesertWarfareEffect(final DesertWarfareEffect effect) {
        super(effect);
    }

    @Override
    public DesertWarfareEffect copy() {
        return new DesertWarfareEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Card card = game.getCard(getTargetPointer().getFirst(game, source));
        if (card == null) {
            return false;
        }
        DelayedTriggeredAbility delayed = new AtTheBeginOfNextEndStepDelayedTriggeredAbility(
                new ReturnToBattlefieldUnderYourControlTargetEffect(), TargetController.YOU
        );
        delayed.getEffects().setTargetPointer(new FixedTarget(card, game));
        game.addDelayedTriggeredAbility(delayed, source);
        return true;
    }
}
