# WS33 G3 non-AF — cost-time ENTITY_LIST_SELECTION root cause

STATUS = ROOT_CAUSE_CONFIRMED
TASK_COMPLETE = NO
WS33_COMPLETE = FALSE
COVERAGE_PROMOTION = FALSE
ACTIVE_PENDING_CHECKPOINT = NONE

## Live boundary before this checkpoint

- BRANCH: `work/ws33-g3-final-closure-20260902`
- HEAD: `7e99c2a498555e7bcdbd3eb39c183baac9d38989`
- TREE: `0d2c0b1d7c0d880fd6a5c948aeb836635f010382`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Last terminal runtime run: `33919282114`
- Job: `101173616625`
- Artifact: `9954643672` (`ws33-g3-svar-event-runtime-33919282114`)
- GitHub digest: `sha256:13322c3ddae4670049e13192303c945e76940cbef4b20c2cd1b417e0468e0d1f`
- Independently downloaded ZIP SHA256: `13322c3ddae4670049e13192303c945e76940cbef4b20c2cd1b417e0468e0d1f`

## Direct runtime facts

Target effective path:

`forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`

Lineage:

`Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`

For triggered DigUntil ability `712`, source trigger `50010`, host `385`, the run emitted:

- `required=1`
- `mandatory=false`
- authoritative sacrifice source IDs: `388`
- authoritative filtered candidates: `388`
- `candidateCount=1`
- selection cancelled
- `decisionNull=true`
- `PAY_COST=false`
- `PREREQUISITES_MET=false`

The corresponding Decision request was `ENTITY_LIST_SELECTION`, min/max `1/1`, but the request exported two generic discrete option IDs `choice:0` and `choice:1`; the record tape selected `choice:0`. No RNG event occurred for this effective path.

Evidence classification: **DIRECTLY_VERIFIED** from run `33919282114`, artifact `9954643672`, and independently re-hashed ZIP.

## Source boundary

Pinned `HumanCostDecision.visit(CostSacrifice)` computes the sacrifice candidates using Forge legality and then constructs `InputSelectCardsFromList(controller, c, c, list, ability)`, sets `cancelAllowed = !mandatory`, calls `showAndWait()`, and returns `null` on cancellation.

The exact WS01 source pin used by the workflow applies `apply-ws01-synchronized-input-bridge.py`. Its `InputSelectEntitiesFromList.driveExternal()` builds an ordered string action list:

1. `DONE` when `hasEnoughTargets()`;
2. `CANCEL` when `allowCancel`;
3. one `ENTITY:<ExternalDecisionRequest.optionIdFor(entity)>` string per authoritative entity.

It then passes that list through `PlayerControllerHuman.chooseExternalUiOptions(..., "ENTITY_LIST_SELECTION", value -> value)`.

For the failing sacrifice state, `hasEnoughTargets()` is false, `allowCancel` is true, and the only legal entity is Card `388`. Therefore the bridge deterministically constructs exactly two UI actions in this order:

- `CANCEL`
- `ENTITY:<Card-388 authoritative option id>`

`chooseExternalUiOptions` converts those authoritative-transition strings into generic discrete IDs (`choice:0`, `choice:1`). The record pilot selected `choice:0`, which the bridge decodes back to `CANCEL`; `onCancel()` sets the legacy input cancellation flag and clears the selection. `HumanCostDecision` consequently returns `null` and Forge does not pay the cost.

Evidence classification: **CODE_DERIVED**, directly grounded in pinned Forge plus exact WS01 overlay source and the run trace.

## Root cause

This is **not an RNG defect** and **not a Forge sacrifice-validity defect**.

The shared synchronized-input adapter erases authoritative entity option identity by embedding the entity ID inside a semantic UI string and then re-wrapping the transition as generic `choice:N` options. It also models cancellation as an ordinary discrete option while the external request itself reports `cancelAllowed=false` (because the bridge passes `false` to `chooseExternalUiOptions`). That shape is inconsistent with the project Decision ABI and allows a qualification pilot selecting an otherwise accepted generic option to resolve to legacy cancellation rather than the sole authoritative entity.

ROOT_CAUSE = `WS01 synchronized InputSelectEntitiesFromList bridge uses generic UI-option encoding for authoritative entity/cancel transitions`

ROOT_BOUNDARY = `InputSelectEntitiesFromList.driveExternal -> PlayerControllerHuman.chooseExternalUiOptions -> generic choice:N response -> CANCEL`

## Repair requirement

Repair the shared external synchronized entity-list binding systemically for this runtime, without card/path branches and without changing Forge legality:

- authoritative `GameEntity` candidates must be exported with `ExternalDecisionRequest.optionIdFor(entity)` / entity kind / entity ID;
- cancellation must use the Decision ABI cancellation channel when `allowCancel`, not a fake `choice:N` option;
- `DONE` may only be exposed when the current Forge input already satisfies its minimum and must remain an explicit authoritative transition;
- selected entity IDs must be mapped back only to the current `validChoices` and fail closed if stale;
- no first/default/random/pass/cancel fallback;
- no automatic singleton selection for this optional/cancellable state;
- Forge remains sole authority for `validChoices`, min/max, and whether cancellation/DONE are legal.

No current official Magic rules adjudication is required for this repair because the repair preserves Forge's already-computed legal candidate set and current cancellation/min/max semantics; it changes only external Decision identity/binding.

SEMANTIC_REPAIR_RESULT = UNKNOWN until the exact-source qualification rerun passes.

## Next action

1. Re-verify live branch HEAD/TREE.
2. Apply exactly one runtime-affecting repair commit to the already-triggering WS33 instrumentation/overlay path.
3. Verify exactly one workflow run for that source commit.
4. Immediately persist `RUN`, `JOB`, `SOURCE_HEAD`, `SOURCE_TREE`, workflow and run cardinality as a `*_PENDING.md` checkpoint, then freeze writes until terminal.
