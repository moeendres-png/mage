# G3 NON-AF — OPTIONAL-COST SINGLETON ROOT CAUSE

Classification: `CODE_DERIVED` + `DIRECTLY_VERIFIED` runtime boundary.

## Runtime evidence consumed

Run `33820842986` proves the first parent exits `PlaySpellAbility.playSpellAbility(...)` at `OPTIONAL_COST_SELECTION_NULL`, before `playAbility(...)` and before any `MagicStack` lifecycle event.

Immutable evidence: artifact `9918266289`, digest `sha256:693c5b2767e3758668dc38183aa21f543ca0fe08faf3d1e2d8d3c3c98154dfa6`.

## Pinned Forge source derivation

Pinned Forge: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.

`GameActionUtil.getAdditionalCostSpell(sa)` initializes `abilities` as exactly `[sa]`. It changes that list only when:

1. `sa.isSpell()` and an `AlternateAdditionalCost` keyword is present; or
2. `sa.isActivatedAbility()` and `AlternateCost` is present.

The production parent admitted by `TriggerHandler` is a `forge.game.trigger.WrappedAbility`. Pinned `WrappedAbility` extends `Ability`, wraps the triggered SpellAbility, and is not a spell or an activated ability. Therefore this call produces exactly one authoritative ability variant for the failing trigger.

`PlaySpellAbility.chooseOptionalAdditionalCosts(...)` nevertheless always calls:

`controller.getAbilityToPlay(original.getHostCard(), abilities)`

before it processes optional keyword costs.

Under the WS01 strict boundary, `PlayerControllerHuman.getGui()` swaps to `ExternalDecisionGuiAdapter` when an external provider is installed, and that adapter explicitly treats legacy `getAbilityToPlay` as unsupported because it lacks a typed response schema. In non-rendering qualification contexts the legacy GUI path can therefore yield no selected ability instead of applying Desktop Forge's singleton behavior.

## Pinned Forge reference behavior

Pinned desktop `CMatchUI.getAbilityToPlay(...)` has an explicit `triggerEvent == null` branch:

- empty list -> null;
- one ability -> return that exact ability;
- more than one -> ask the user to choose one or none.

`PlaySpellAbility.chooseOptionalAdditionalCosts` invokes `getAbilityToPlay(host, abilities)` without a trigger event, so the failing singleton is non-discretionary in the authoritative pinned GUI behavior.

## Repair adjudication

Authorized systemic repair:

In pinned `PlaySpellAbility.chooseOptionalAdditionalCosts`, bypass the GUI/controller ability-selection surface only when `abilities.size() == 1`, returning `abilities.get(0)` as the selected variant. Preserve existing behavior for `0` and `>1` options.

This is NOT a silent `first/default` fallback:

- it never selects among multiple options;
- it preserves the exact sole Rules-Core-produced object;
- it matches pinned Desktop Forge behavior for the same no-trigger-event call;
- it does not change legality, costs, targets, timing, trigger admission, stack order, Decision/RNG, or coverage;
- genuinely discretionary multi-option ability variants remain routed to the existing controller/strict decision boundary and are not auto-selected.

No card/path names participate in the repair.

## Next gate

Implement this as a focused WS33 runtime overlay, then trigger exactly one non-AF event-runtime successor. Immediately checkpoint run/job/source HEAD/TREE. If the first failure advances (expected candidate: later `SETUP_TARGETS=false` parents), freeze and diagnose that new boundary before any further repair.

`G3_NON_AF_STATUS = UNKNOWN`
`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
