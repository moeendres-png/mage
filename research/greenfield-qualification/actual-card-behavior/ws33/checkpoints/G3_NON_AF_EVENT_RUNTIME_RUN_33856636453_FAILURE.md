# WS33 G3 non-AF event runtime — run 33856636453 failure

Status: `FAIL / BEHAVIOR-BEARING DIAGNOSTIC / NO COVERAGE PROMOTION`

## Immutable identity

- run: `33856636453`
- job: `100971364332`
- source HEAD: `f14d7a58eedcf781c20d40be9889e31dd86b5d13`
- source TREE: `aef8a3a1af673627b1cb9dc0f7080f665d1b5248`
- artifact: `9930644194`
- artifact digest: `sha256:75a3cd584b0d3184e82cd3ede5446fbbc573801bc713c2a37c0b136dcaaebbdb`
- independently downloaded ZIP SHA256: `75a3cd584b0d3184e82cd3ede5446fbbc573801bc713c2a37c0b136dcaaebbdb` — exact match

## Step adjudication

- Steps 1–14: PASS
- Step 15 strict record adjudication: FAIL
- replay/source-chain: SKIPPED
- evidence upload: PASS

The record result remains exactly one failing production parent/effective path:

- parents: `32/33 PASS`
- effective paths: `31/32 PASS`
- sole failure: `Study Hall / SpellCast / SVAR TrigSpent -> TrigScry / Scry`
- source-proven admission/binding/execution: `0/0/0`

No partial PASS is promoted.

## Direct spawned-trigger gate evidence

Same-run `record/runtime.log` contains observation-only `WS33_TRIGGER_GATE` telemetry for dynamic trigger `50038` hosted/spawned by Study Hall.

Observed counts:

- `ACTIVE_PASS=true`: 402
- `CAN_MODE=false`: 398 — expected checks against unrelated TriggerWaiting modes
- `CAN_PERFORM_TEST=false`: 4 — actual SpellCast-mode checks
- `CAN_PASS`: 0

Therefore:

1. `isTriggerActive(...)` is not the blocker;
2. the dynamic trigger reaches `canRunTrigger(...)` under matching `SpellCast` mode;
3. suppression, activation limit, common requirements, triggered-object requirements, and mode checks all pass for those matching checks;
4. the remaining production rejection is inside `TriggerSpellAbilityCastOrCopy.performTest(...)`.

Pinned Study Hall `TrigSpent` has only the relevant filters `ValidCard$ Card.IsCommander+YouOwn` and `ValidActivatingPlayer$ You`, plus the generic `TriggersWhenSpent` remembered-spell identity check imposed by `TriggerSpellAbilityCastOrCopy` when `getSpawningAbility()!=null` and the spawning ability has `TriggersWhenSpent`.

The exact failing performTest subcondition is not yet directly observed. Do not repair by inference.

## Exact next action

Add observation-only diagnostics inside pinned `TriggerSpellAbilityCastOrCopy.performTest(...)`, limited to dynamically spawned triggers, sufficient to distinguish:

- missing `SpellAbility` runParam;
- `ValidActivatingPlayer` mismatch;
- `ValidCard` mismatch;
- spawned `TriggersWhenSpent` remembered-spell identity mismatch.

Preserve every production boolean expression and return ordering. One diagnostic commit -> exactly one successor run -> immediate pending checkpoint -> terminal artifact adjudication before any repair.

`G3_NON_AF_STATUS = UNKNOWN`
`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
