# WS85 Implementation (pure future-state probe)

Production files modified (7):

1. `Mage/src/main/java/mage/abilities/effects/ContinuousEffect.java`
   - New default method `wouldRemoveEnteringAbility(entering, enteringAbility,
     source, game)` (default false: no evidence of removal). Pure observational
     contract in javadoc: no battlefield insertion, no apply() call, no mutation
     of any object; errors propagate, never swallowed.

2. `Mage/src/main/java/mage/abilities/effects/ContinuousEffects.java`
   - `isSelfEnteringReplacementWithoutFutureAbility`: same ETB/self-scope/
     target==source gating; null effect/ability/event/game now throw
     IllegalStateException (explicit programming-error failure); defined
     non-applicability inputs return false. No try/catch. Reentrancy guard
     removed (pure probe cannot reenter replacement filtering).
   - `wouldLoseEnteringAbilityViaPreexistingLayer6`: evaluates a detached
     `entering.copy()` (never inserted anywhere) through each pre-existing
     usable layer-6 LoseAbility remover's own pure probe, in getOrder order.
     No addPermanent/removePermanent, no remover.apply, no ability-list writes.
   - Prevention loop: shared helper call kept (pure now; unreachable for
     damage-only prevention today; documented future-proofing).

3. `Mage/src/main/java/mage/abilities/effects/common/continuous/LoseAllAbilitiesAllEffect.java`
   - Pure probe = same `filter.match(enteringView, controller, source, game)`
     that `apply()` loops over.

4. `Mage/src/main/java/mage/abilities/effects/common/continuous/LoseAbilityAllEffect.java`
   - Pure probe mirrors apply()'s affected-object determination: fixed-set MORs
     resolved read-only (no prune, no discard); dynamic branch uses same filter
     + excludeSource; suppression only when the entering ability isSameInstance
     matches a removed ability (same matching removeAbility uses).

5. `Mage/src/main/java/mage/abilities/effects/common/continuous/LoseAbilityTargetEffect.java`
   - Pure probe = read-only target-pointer contains(entering) + isSameInstance
     ability check. No removal.

6. `Mage.Sets/src/mage/cards/h/Humility.java` (HumilityEffect)
   - Pure probe = same StaticFilters.FILTER_PERMANENT_CREATURE the layer-6
     branch loops over + same null-controller guard. No battlefield iteration,
     no removal. (Effect-owned logic; no card-name branch in shared code.)

7. `Mage/src/main/java/mage/abilities/effects/ReplacementEffectImpl.java`
   - Comment only: bounds the claim to the layer-6 ability-removal subset;
     full general projection explicitly out of scope.

Deliberately NOT overridden (default false is faithful or safe-allow):
LoseAbilitySourceEffect / LoseAbilityAttachedEffect / LoseAllAbilitiesAttachedEffect
(single-object effects whose apply() no-ops for non-member entering objects),
Yixlid-style graveyard customs (battlefield entering never in scope),
LoseAllAbilitiesTargetEffect (Outcome.AddAbility: excluded by the LoseAbility
gate in both old and new code), CreaturesCantGetOrHaveAbilityEffect
(Outcome.Detriment: excluded by the gate).

Failure semantics: no catch-and-allow anywhere on the probe path. Defined
non-applicability returns false with no removal claimed; remover evaluation
errors propagate as explicit engine failures. Suppression requires positive
pure-match evidence only.

Tests added (1 file, `Mage.Tests/.../serverside/ws85/WS85FutureStateHardeningTest.java`):
P0 sentinel control (neutrality + non-vacuity), P1 purity (dual-presence flag +
H01-A outcome), P2 actual-card live-state snapshot (membership/abilities/
controller/stack/entering-map hygiene), F1 failure semantics (injected marker
must propagate; no fabricated copy; no partial mutation).

Second Rules engine: none (selection/gating + per-effect pure predicates only).
Card-name hacks: none (verified by diff grep; reviewer-confirmed).
