package mage.abilities.effects.common;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.abilities.DelayedTriggeredAbility;
import mage.abilities.effects.ContinuousRuleModifyingEffectImpl;
import mage.abilities.effects.OneShotEffect;
import mage.constants.Duration;
import mage.constants.Outcome;
import mage.constants.Zone;
import mage.game.Game;
import mage.game.events.GameEvent;
import mage.game.events.ZoneChangeEvent;
import mage.game.permanent.Permanent;

/**
 * Untap the target permanent, then it phases out and stays phased out as long as the source permanent holds it
 * (The Moment, The Pandorica):
 * <ul>
 * <li>it does not phase in during its controller's untap step while the source is on the battlefield
 * (and, with whileSourceTapped, tapped);</li>
 * <li>it phases in as soon as the source leaves the battlefield (and, with whileSourceTapped, becomes untapped).</li>
 * </ul>
 * If the source has already left the battlefield when the effect resolves, the target is untapped but does not
 * phase out.
 */
public class PhaseOutHeldBySourceEffect extends OneShotEffect {

    private final boolean whileSourceTapped;

    /**
     * @param whileSourceTapped true: the target also phases in when the source becomes untapped
     */
    public PhaseOutHeldBySourceEffect(boolean whileSourceTapped) {
        super(Outcome.Detriment);
        this.whileSourceTapped = whileSourceTapped;
        this.staticText = whileSourceTapped
                ? "untap another target nonland permanent, then it phases out. It can't phase in for as long as {this} remains tapped. "
                + "When {this} becomes untapped or leaves the battlefield, that permanent phases in"
                : "untap target creature you control. It phases out until {this} leaves the battlefield";
    }

    private PhaseOutHeldBySourceEffect(final PhaseOutHeldBySourceEffect effect) {
        super(effect);
        this.whileSourceTapped = effect.whileSourceTapped;
    }

    @Override
    public PhaseOutHeldBySourceEffect copy() {
        return new PhaseOutHeldBySourceEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        Permanent target = game.getPermanent(getTargetPointer().getFirst(game, source));
        if (target == null) {
            return false;
        }
        target.untap(game);
        Permanent holder = source.getSourcePermanentIfItStillExists(game);
        if (holder == null) {
            return true;
        }
        if (!target.phaseOut(game)) {
            return true;
        }
        game.processAction();
        MageObjectReference held = new MageObjectReference(target, game);
        game.addEffect(new HoldPhasedOutEffect(held, whileSourceTapped), source);
        game.addDelayedTriggeredAbility(new ReleasePhasedOutAbility(held, whileSourceTapped), source);
        return true;
    }

    static boolean sourceHolds(MageObjectReference held, boolean whileSourceTapped, Ability source, Game game) {
        Permanent holder = source.getSourcePermanentIfItStillExists(game);
        return holder != null && (!whileSourceTapped || holder.isTapped());
    }

    static class HoldPhasedOutEffect extends ContinuousRuleModifyingEffectImpl {

        private final MageObjectReference held;
        private final boolean whileSourceTapped;

        HoldPhasedOutEffect(MageObjectReference held, boolean whileSourceTapped) {
            super(Duration.Custom, Outcome.Detriment, false, false);
            this.held = held;
            this.whileSourceTapped = whileSourceTapped;
        }

        private HoldPhasedOutEffect(final HoldPhasedOutEffect effect) {
            super(effect);
            this.held = effect.held;
            this.whileSourceTapped = effect.whileSourceTapped;
        }

        @Override
        public HoldPhasedOutEffect copy() {
            return new HoldPhasedOutEffect(this);
        }

        @Override
        public boolean checksEventType(GameEvent event, Game game) {
            return event.getType() == GameEvent.EventType.PHASE_IN;
        }

        @Override
        public boolean applies(GameEvent event, Ability source, Game game) {
            return event.getTargetId().equals(held.getSourceId())
                    && held.getPermanent(game) != null
                    && sourceHolds(held, whileSourceTapped, source, game);
        }

        @Override
        public boolean isInactive(Ability source, Game game) {
            Permanent permanent = held.getPermanent(game);
            return permanent == null || permanent.isPhasedIn();
        }
    }

    static class ReleasePhasedOutAbility extends DelayedTriggeredAbility {

        private final MageObjectReference held;
        private final boolean whileSourceTapped;

        ReleasePhasedOutAbility(MageObjectReference held, boolean whileSourceTapped) {
            super(new ReleasePhasedOutEffect(held), Duration.OneUse);
            this.held = held;
            this.whileSourceTapped = whileSourceTapped;
            this.usesStack = false;
            this.setRuleVisible(false);
        }

        private ReleasePhasedOutAbility(final ReleasePhasedOutAbility ability) {
            super(ability);
            this.held = ability.held;
            this.whileSourceTapped = ability.whileSourceTapped;
        }

        @Override
        public ReleasePhasedOutAbility copy() {
            return new ReleasePhasedOutAbility(this);
        }

        @Override
        public boolean checkEventType(GameEvent event, Game game) {
            return event.getType() == GameEvent.EventType.ZONE_CHANGE
                    || (whileSourceTapped && event.getType() == GameEvent.EventType.UNTAPPED);
        }

        @Override
        public boolean checkTrigger(GameEvent event, Game game) {
            if (!event.getTargetId().equals(getSourceId())) {
                return false;
            }
            if (event.getType() == GameEvent.EventType.UNTAPPED) {
                return true;
            }
            return ((ZoneChangeEvent) event).getFromZone() == Zone.BATTLEFIELD;
        }
    }

    static class ReleasePhasedOutEffect extends OneShotEffect {

        private final MageObjectReference held;

        ReleasePhasedOutEffect(MageObjectReference held) {
            super(Outcome.Benefit);
            this.held = held;
        }

        private ReleasePhasedOutEffect(final ReleasePhasedOutEffect effect) {
            super(effect);
            this.held = effect.held;
        }

        @Override
        public ReleasePhasedOutEffect copy() {
            return new ReleasePhasedOutEffect(this);
        }

        @Override
        public boolean apply(Game game, Ability source) {
            Permanent permanent = held.getPermanent(game);
            if (permanent != null && !permanent.isPhasedIn()) {
                permanent.phaseIn(game);
            }
            return true;
        }
    }
}
