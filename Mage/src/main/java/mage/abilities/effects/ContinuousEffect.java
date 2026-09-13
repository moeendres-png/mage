package mage.abilities.effects;

import mage.MageObjectReference;
import mage.abilities.Ability;
import mage.constants.DependencyType;
import mage.constants.Duration;
import mage.constants.Layer;
import mage.constants.SubLayer;
import mage.game.Game;
import mage.game.permanent.Permanent;
import mage.target.targetpointer.TargetPointer;

import java.util.EnumSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;

/**
 * @author BetaSteward_at_googlemail.com
 */
public interface ContinuousEffect extends Effect {

    boolean isUsed();

    boolean isDiscarded();

    void discard();

    ContinuousEffect setDuration(Duration duration);

    Duration getDuration();

    long getOrder();

    void setOrder(long order);

    boolean apply(Layer layer, SubLayer sublayer, Ability source, Game game);

    boolean hasLayer(Layer layer);

    /**
     * CR 614.12 future-state applicability probe (pure, observational).
     *
     * <p>Answers whether this effect would remove the given entering ability from the
     * given entering permanent once that permanent exists on the battlefield, WITHOUT
     * mutating any live game state: no battlefield insertion, no {@code apply()} call,
     * no ability removal, no trigger/event/stack/RNG effects. Implementations must answer
     * solely from their own filter/target state (the same state {@code apply()} uses).
     *
     * <p>The entering permanent passed in is a detached hypothetical view (a copy), never
     * a live battlefield member; implementations must not add it to the battlefield and
     * must not modify it, the game, or any other object.
     *
     * <p>Evaluation errors must propagate to the caller; implementations must not swallow
     * them into a fabricated answer. Effects without a meaningful pure answer for an
     * entering object keep the default ({@code false}: no evidence of removal).
     *
     * @param entering         detached hypothetical view of the entering permanent
     * @param enteringAbility  the self entering replacement's source ability under test
     * @param source           the ability this effect originates from
     * @param game             current game (read-only use)
     * @return true only on positive evidence that this effect would remove the ability
     */
    default boolean wouldRemoveEnteringAbility(Permanent entering, Ability enteringAbility, Ability source, Game game) {
        return false;
    }

    boolean isInactive(Ability source, Game game);

    /**
     * Init ability data like ZCC or targets on first check in game cycle (ApplyEffects)
     * <p>
     * Warning, if you setup target pointer in init then must call super.init at the end (after all choices)
     */
    void init(Ability source, Game game);

    void init(Ability source, Game game, UUID activePlayerId);

    Layer getLayer();

    SubLayer getSublayer();

    List<MageObjectReference> getAffectedObjects();

    Set<UUID> isDependentTo(List<ContinuousEffect> allEffectsInLayer);

    EnumSet<DependencyType> getDependencyTypes();

    void addDependencyType(DependencyType dependencyType);

    void setDependedToType(DependencyType dependencyType);

    EnumSet<DependencyType> getDependedToTypes();

    void addDependedToType(DependencyType dependencyType);

    void setStartingControllerAndTurnNum(Game game, UUID startingController, UUID activePlayerId);

    UUID getStartingController();

    boolean isYourNextTurn(Game game);

    boolean isYourNextEndStep(Game game);

    boolean isYourNextUpkeepStep(Game game);

    @Override
    ContinuousEffect copy();

    boolean isTemporary();

    void setTemporary(boolean temporary);

    @Override
    ContinuousEffect setTargetPointer(TargetPointer targetPointer);
}
