package mage.abilities.common;

import mage.abilities.TriggeredAbilityImpl;
import mage.abilities.effects.Effect;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.permanent.Permanent;
import mage.target.targetpointer.FixedTarget;

/**
 * "Whenever a creature you control connives, ..."
 * The target pointer (when set) points to the creature that connived.
 */
public class ConnivesCreatureYouControlTriggeredAbility extends TriggeredAbilityImpl {

    private final boolean setTargetPointer;

    public ConnivesCreatureYouControlTriggeredAbility(Effect effect, boolean optional, boolean setTargetPointer) {
        super(Zone.BATTLEFIELD, effect, optional);
        this.setTargetPointer = setTargetPointer;
        setTriggerPhrase("Whenever a creature you control connives, ");
    }

    private ConnivesCreatureYouControlTriggeredAbility(final ConnivesCreatureYouControlTriggeredAbility ability) {
        super(ability);
        this.setTargetPointer = ability.setTargetPointer;
    }

    @Override
    public boolean checkEventType(GameEvent event, Game game) {
        return event.getType() == GameEvent.EventType.CONNIVED;
    }

    @Override
    public boolean checkTrigger(GameEvent event, Game game) {
        if (!isControlledBy(event.getPlayerId())) {
            return false;
        }
        Permanent permanent = game.getPermanentOrLKIBattlefield(event.getTargetId());
        if (permanent == null || !permanent.isCreature(game)) {
            return false;
        }
        if (setTargetPointer) {
            getEffects().setTargetPointer(new FixedTarget(permanent, game));
        }
        return true;
    }

    @Override
    public ConnivesCreatureYouControlTriggeredAbility copy() {
        return new ConnivesCreatureYouControlTriggeredAbility(this);
    }
}
