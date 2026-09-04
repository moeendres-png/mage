# WS33 G3 non-AF — authoritative entity-list repair PENDING

STATUS = PENDING
TASK_COMPLETE = NO
WS33_COMPLETE = FALSE
COVERAGE_PROMOTION = FALSE

## Repair source

- runtime-affecting repair commit: `2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7`
- SOURCE_HEAD: `2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7`
- SOURCE_TREE: `fbb9565d4583db655872cfd378831711b0989b7a`
- commit message: `ws33 g3: preserve authoritative entity identity in synchronized inputs`
- changed runtime-triggering file: `research/greenfield-qualification/actual-card-behavior/ws33/ws33_instrument_g_authoritative_requests.py`
- parent: `a82c0691d563b351752430fcb877042bed49fc6f`

## Qualification run

- workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- workflow name: `WS33 G3 SVar non-AF event runtime`
- RUN: `33928315020`
- JOB: `101201530278`
- event: `push`
- run attempt: `1`
- observed status at checkpoint creation: `in_progress`
- exact-source run cardinality for `2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7`: `1`

Run cardinality classification: **DIRECTLY_VERIFIED** from GitHub Actions filtered by exact `head_sha`.

## Repair contract being tested

The repair replaces the WS01 synchronized `InputSelectEntitiesFromList` bridge's generic `choice:N` action encoding with a typed external entity request:

- Forge `validChoices` remains authoritative;
- entity option IDs are `ExternalDecisionRequest.optionIdFor(entity)` with authoritative kind/id;
- min/max remain the current Forge input bounds;
- cancellation is carried by the Decision ABI `cancelAllowed`/cancel response channel, not a fake discrete option;
- the existing strict input `applyExternalSelection` / `applyExternalCancel` revalidates count, membership, staleness and cancel legality;
- principal-scoped card observation lifetime is retained around the request;
- no card name, effective path ID, first/default/random/pass/cancel fallback, rules mutation, RNG mutation or coverage mutation is introduced.

Semantic result remains **UNKNOWN** until the run is terminal and its immutable artifact is independently adjudicated.

## Write freeze

`WRITE_FREEZE = TRUE`

No further runtime-affecting or qualification-state writes are permitted until run `33928315020` is terminal. On terminal state, first persist RUN/JOB/SOURCE_HEAD/SOURCE_TREE/artifact/name/GitHub digest/independent ZIP SHA256 and first material failure or exact PASS gates, then update the continuation handoff before any subsequent repair.
