package mage.abilities.effects.common.continuous;

import mage.abilities.Ability;
import mage.abilities.Mode;
import mage.abilities.effects.ContinuousEffectImpl;
import mage.constants.Duration;
import mage.constants.Layer;
import mage.constants.Outcome;
import mage.constants.SubLayer;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.util.CardUtil;

import java.util.UUID;

/**
 * @author jeffwadsworth
 */
public class LoseAbilityTargetEffect extends ContinuousEffectImpl {

    private final Ability ability;

    public LoseAbilityTargetEffect(Ability ability, Duration duration) {
        super(duration, Layer.AbilityAddingRemovingEffects_6, SubLayer.NA, Outcome.LoseAbility);
        this.ability = ability;
    }

    protected LoseAbilityTargetEffect(final LoseAbilityTargetEffect effect) {
        super(effect);
        this.ability = effect.ability.copy();
    }

    @Override
    public LoseAbilityTargetEffect copy() {
        return new LoseAbilityTargetEffect(this);
    }

    @Override
    public boolean apply(Game game, Ability source) {
        boolean result = false;
        for (UUID uuid : getTargetPointer().getTargets(game, source)) {
            Permanent permanent = game.getPermanent(uuid);
            if (permanent != null) {
                permanent.removeAbility(ability, source.getSourceId(), game);
                result = true;
            }
        }
        return result;
    }

    /**
     * Pure CR 614.12 probe: reports removal only when the entering object is among the
     * effect's targets (read-only pointer resolution, no removal) and the entering
     * ability is an instance the effect would remove (same {@code isSameInstance}
     * matching {@code removeAbility} uses).
     */
    @Override
    public boolean wouldRemoveEnteringAbility(Permanent entering, Ability enteringAbility, Ability source, Game game) {
        if (entering == null || enteringAbility == null || source == null || game == null) {
            return false;
        }
        if (!getTargetPointer().getTargets(game, source).contains(entering.getId())) {
            return false;
        }
        return enteringAbility.isSameInstance(ability);
    }

    @Override
    public String getText(Mode mode) {
        if (staticText != null && !staticText.isEmpty()) {
            return staticText;
        }
        return getTargetPointer().describeTargets(mode.getTargets(), "it")
                + " loses " + CardUtil.stripReminderText(ability.getRule())
                + (duration.toString().isEmpty() ? "" : ' ' + duration.toString());
    }
}
