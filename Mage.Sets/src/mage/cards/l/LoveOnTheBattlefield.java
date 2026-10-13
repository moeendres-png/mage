package mage.cards.l;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.DelayedTriggeredAbility;
import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.effects.OneShotEffect;
import mage.abilities.effects.common.continuous.GainAbilityTargetEffect;
import mage.abilities.effects.common.counter.AddCountersTargetEffect;
import mage.abilities.keyword.FirstStrikeAbility;
import mage.cards.CardImpl;
import mage.cards.CardSetInfo;
import mage.constants.CardType;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.counters.CounterType;
import mage.game.Game;
import mage.game.events.DamagedEvent;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.players.Player;
import mage.target.targetpointer.FixedTarget;
import mage.target.targetpointer.FixedTargets;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * @author commander-lab
 */
public final class LoveOnTheBattlefield extends CardImpl {

    public LoveOnTheBattlefield(UUID ownerId, CardSetInfo setInfo) {
        super(ownerId, setInfo, new CardType[]{CardType.ENCHANTMENT}, "{1}{U}{R}");

        // Whenever you attack with exactly two creatures, those creatures gain first strike until end of turn, then draw a card. Whenever either of those creatures deals combat damage to a player this combat, put a +1/+1 counter on it.
        this.addAbility(new LoveOnTheBattlefieldTriggeredAbility());
    }

    private LoveOnTheBattlefield(final LoveOnTheBattlefield card) {
        super(card);
    }

    @Override
    public LoveOnTheBattlefield copy() {
        return new LoveOnTheBattlefield(this);
    }
}

class LoveOnTheBattlefieldTriggeredAbility extends TriggeredAbilityImpl {

    LoveOnTheBattlefieldTriggeredAbility() {
        super(Zone.BATTLEFIELD, new LoveOnTheBattlefieldEffect(), false);
        setTriggerPhrase("Whenever you attack with exactly two creatures, ");
    }

    private LoveOnTheBattlefieldTriggeredAbility(final LoveOnTheBattlefieldTriggeredAbility ability) {
        super(ability);
    }

    @Override
    public LoveOnTheBattlefieldTriggeredAbility copy() {
        return new LoveOnTheBattlefieldTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DECLARED_ATTACKERS;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!isControlledBy(game.getCombat().getAttackingPlayerId())) {
            return false;
        }
        List<Permanent> attackers = game.getCombat().getAttackers()
                .stream()
                .map(game::getPermanent)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
        if (attackers.size() != 2) {
            return false;
        }
        getEffects().setTargetPointer(new FixedTargets(attackers, game));
        return true;
    }
}

class LoveOnTheBattlefieldEffect extends OneShotEffect {

    LoveOnTheBattlefieldEffect() {
        super(Outcome.BoostCreature);
        staticText = "those creatures gain first strike until end of turn, then draw a card. Whenever either "
                + "of those creatures deals combat damage to a player this combat, put a +1/+1 counter on it";
    }

    private LoveOnTheBattlefieldEffect(final LoveOnTheBattlefieldEffect effect) {
        super(effect);
    }

    @Override
    public LoveOnTheBattlefieldEffect copy() {
        return new LoveOnTheBattlefieldEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Player controller = game.getPlayer(source.getControllerId());
        if (controller == null) {
            return false;
        }
        List<Permanent> creatures = getTargetPointer().getTargets(game, source)
                .stream()
                .map(game::getPermanent)
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
        if (!creatures.isEmpty()) {
            game.addEffect(new GainAbilityTargetEffect(FirstStrikeAbility.getInstance(), Duration.EndOfTurn)
                    .setTargetPointer(new FixedTargets(creatures, game)), source);
        }
        controller.drawCards(1, source, game);
        List<MageObjectReference> refs = new ArrayList<>();
        for (Permanent creature : creatures) {
            refs.add(new MageObjectReference(creature, game));
        }
        game.addDelayedTriggeredAbility(new LoveOnTheBattlefieldDelayedTriggeredAbility(refs), source);
        return true;
    }
}

class LoveOnTheBattlefieldDelayedTriggeredAbility extends DelayedTriggeredAbility {

    private final List<MageObjectReference> creatures;

    LoveOnTheBattlefieldDelayedTriggeredAbility(List<MageObjectReference> creatures) {
        super(new AddCountersTargetEffect(CounterType.P1P1.createInstance()), Duration.EndOfCombat, false);
        this.creatures = creatures;
        setTriggerPhrase("Whenever either of those creatures deals combat damage to a player this combat, ");
    }

    private LoveOnTheBattlefieldDelayedTriggeredAbility(final LoveOnTheBattlefieldDelayedTriggeredAbility ability) {
        super(ability);
        this.creatures = new ArrayList<>(ability.creatures);
    }

    @Override
    public LoveOnTheBattlefieldDelayedTriggeredAbility copy() {
        return new LoveOnTheBattlefieldDelayedTriggeredAbility(this);
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.DAMAGED_PLAYER;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!((DamagedEvent) event).isCombatDamage()) {
            return false;
        }
        for (MageObjectReference mor : creatures) {
            if (mor.refersTo(event.getSourceId(), game)) {
                Permanent permanent = mor.getPermanent(game);
                if (permanent == null) {
                    return false;
                }
                getEffects().setTargetPointer(new FixedTarget(permanent, game));
                return true;
            }
        }
        return false;
    }
}
