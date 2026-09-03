# WS33 G3 — NON-AF EVENT CASE ABI V2

Evidence classification: `CODE_DERIVED`. No runtime qualification or global coverage promotion is claimed here.

## Boundary

- branch: `work/ws33-g3-final-closure-20260902`
- input post-AF handoff HEAD: `ce5c0fac4e55e8ea63faca1f456d252e9e71be69`
- event-case ABI repair commit: `b406f1310c6a644cc52d5a6b4af3f38725abbaf5`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- topology artifact: `9866293827`
- topology digest: `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`

## Defect closed

The pre-existing `ws33_prepare_g_svar_event_cases.py` retained a parent script and directive but omitted `parent_svar`. That was insufficient for the one source-proven `SVAR` event parent (`Study Hall` / `TrigSpent`) because its production chain is created by `TriggersWhenSpent`; a harness must not guess or reconstruct the named producer from detached text.

ABI v2 now:

- retains `parent_svar` explicitly as field 13;
- requires every `SVAR` parent to have a non-empty exact name;
- forbids a non-SVAR parent from carrying a name;
- fail-closes unless the frozen topology still yields exactly one named parent-SVar entrypoint;
- keeps all 32 effective paths / 33 real parent entrypoints, including both Kang Prime parents;
- emits `case_field_count = 21` and `schema = commander-simulator-next.ws33-g-svar-event-cases.v2`;
- retains `coverage_mutated=false` and `direct_target_svar_entry=false`.

## Production-boundary source adjudication

Pinned Forge source confirms:

- `TriggerHandler.runTrigger(...)` is the central trigger dispatcher and retains activation-zone, requirement, triggering-object and `performTest` authority before a trigger is run.
- `AbilityManaPart.addTriggersWhenSpent(...)` creates the named `TriggersWhenSpent` trigger from the source SVar and registers it as a this-turn delayed trigger; therefore Study Hall must traverse this producer boundary rather than arbitrary detached trigger registration.

## Status

- Event-case identity ABI: `READY_V2`.
- non-AF runtime qualification: `UNKNOWN/OPEN`.
- global G3 promotion: `FALSE`.
- `WS33_COMPLETE = FALSE`.
- `TASK_COMPLETE = NO`.

## Exact next step

Create a source-parent event harness that consumes ABI v2, binds each actual-card trigger by exact parent identity, invokes the Forge trigger dispatcher with mode-appropriate event facts while leaving all trigger legality to Forge, traverses the real `TriggersWhenSpent` producer for the named-SVar case, and observes the target SVar only through runtime resolution. Commit harness + focused workflow before starting the first run.
