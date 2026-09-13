package mage.abilities.effects;

import mage.abilities.Ability;
import mage.constants.Duration;
import mage.constants.EffectType;
import mage.constants.Outcome;
import mage.game.Game;

/**
 * @author BetaSteward_at_googlemail.com
 */
public abstract class ReplacementEffectImpl extends ContinuousEffectImpl implements ReplacementEffect {

    // 614.12 (current)
    // Some replacement effects modify how a permanent enters the battlefield. (See rules 614.1c-d.)
    // Such effects may come from the permanent itself if they affect only that permanent (as opposed
    // to a general subset of permanents that includes it). They may also come from other sources. To
    // determine which replacement effects apply and how they apply, check the characteristics of the
    // permanent as it would exist on the battlefield, taking into account replacement effects that have
    // already modified how it enters the battlefield (see rule 616.1), continuous effects from the
    // permanent's own static abilities that would apply to it once it's on the battlefield, and
    // continuous effects that already exist and would apply to the permanent.
    // (ContinuousEffects establishes self-scope entering applicability on this basis
    // for the bounded layer-6 ability-removal subset; see
    // CR61412_LAYER6_ABILITY_REMOVAL_SUPPORT. Full general future-state projection
    // is explicitly out of scope.)
    protected boolean selfScope;

    protected ReplacementEffectImpl(Duration duration, Outcome outcome) {
        this(duration, outcome, true);
    }

    /**
     * @param duration
     * @param outcome
     * @param selfScope - is only relevant while permanents entering the
     *                  battlefield events
     */
    protected ReplacementEffectImpl(Duration duration, Outcome outcome, boolean selfScope) {
        super(duration, outcome);
        this.effectType = EffectType.REPLACEMENT;
        this.selfScope = selfScope;
    }

    protected ReplacementEffectImpl(final ReplacementEffectImpl effect) {
        super(effect);
        this.selfScope = effect.selfScope;
    }

    @Override
    public boolean hasSelfScope() {
        return selfScope;
    }

    @Override
    public final boolean apply(Game game, Ability source) {
        throw new UnsupportedOperationException("Wrong code usage: apply() not used for replacement effect.");
    }

}
