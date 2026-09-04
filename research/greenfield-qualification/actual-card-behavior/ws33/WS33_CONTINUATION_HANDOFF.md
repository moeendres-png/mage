# WS33 CONTINUATION HANDOFF

## Completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

Only the final serial `G3 -> ABC -> D -> E -> F` successor with all 4188 effective paths PASS, zero UNKNOWN/FAIL/UNSUPPORTED, A-H UNKNOWN zero, exact pin/model/lineage, and all replay/hidden/RNG/decision/failure/evidence/hash gates may change these flags.

## Stable predecessor

- effective `4188`; PASS `285`; UNKNOWN `3903`; FAIL `0`; UNSUPPORTED `0`; G UNKNOWN `81`; H UNKNOWN `0`.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- effective-manifest file SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- topology consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`.
- predecessor artifact `9823383539`, digest `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`.

## Current confirmed checkpoint

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_RUN_33853539153_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33853539153_FAILURE.md`

Run `33853539153` / job `100961524939` is terminal `failure`.

- source HEAD `98bf38cf6c97f81faacfdefd40b718909ae5494d`
- source TREE `5fe6275585d6068d2fa92166fcf4693672b90c5b`
- artifact `9929351802`
- digest `sha256:126138f1ec2a6c84bad1f823c9814eeaf8213adb4815dbe67181f5a911ae6107`
- downloaded ZIP re-hash: exact match
- Steps 1–14 PASS
- Step 15 FAIL
- replay/source-chain skipped
- evidence upload PASS
- coverage promotion FALSE

### Attempt-13 material result

The qualified principal-observation/lifetime stack fixed the preceding hidden-card boundary. The record campaign completes successfully and the strict parent adjudicator now sees:

- 33 production parents total
- 25 parent PASS / 8 parent FAIL
- 32 effective paths total
- 24 path PASS / 8 path FAIL

No partial PASS is promoted.

Remaining parent failures partition as:

- 5 `Phase` parents with source-proven admission count 0;
- 2 `AttackersDeclared` parents with `Player cannot be cast to Iterable` from the runParam shape;
- 1 `Study Hall` `SpellCast`/`SVAR TrigSpent` parent with admission count 0 whose exact `canRunTrigger` rejection condition remains UNKNOWN.

The five Phase failures are code-derived to a systemic harness ordering defect: `resetActiveTriggers()` is currently called before the target `devModeSet(...)`, while pinned Forge `isTriggerActive()` evaluates `phasesCheck(game)` during registration. The Phase precondition must be established before active-trigger rebuild.

The two AttackersDeclared failures are code-derived to a systemic runParam-shape defect: harness stores scalar `Player` in `AbilityKey.AttackedTarget`; pinned production `PhaseHandler` stores the aggregate attacked-target collection and `TriggerAttackersDeclared.setTriggeringObjects()` casts it to `Iterable<GameEntity>`.

Do not repair Study Hall by card name or inference. Add observation-only expected-trigger rejection telemetry if needed to identify its exact gate.

## Invalid run excluded

Run `33853430763` / job `100961180376` came from a workflow rewrite with a truncated `DIRECT_RUNTIME_SOURCE_HEAD` and is permanently classified `INVALID / NOT QUALIFICATION EVIDENCE`.

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33853430763_INVALID_PRE_RUNTIME.md`

The exact source pin was restored before eligible run `33853539153`.

## Frozen system repairs already validated

### Non-discretionary singleton trigger-play selection

Pinned Forge has exactly one playable additional-cost variant for these trigger wrappers. Desktop Forge returns a singleton without discretionary UI. The strict external path now preserves only that `size()==1` non-choice behavior; empty and multi-option paths remain unchanged/fail-closed. Attempt 11 proved the former first parent (`Ingenious Smith`) advances to admission/binding/execution `1/1/1`.

### Principal-scoped hidden-card observation/lifetime

Non-AF runtime now reuses the same qualified stack as Direct-G/AF:

1. `apply-ws33-observation-fanout.py`
2. `apply-ws33-external-card-decision-lifetime.py`

Both PASS in run `33853539153` with zero rules mutation and zero pilot fallback. Step 14 record PASS confirms the old Dig hidden-card blocker is crossed.

## G3 immutable evidence — do not rerun without invalidation

### Topology

- run `33681121017` SUCCESS; job `100417671589`; artifact `9866293827`; digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`.
- partition `G81 = Direct28 + SVar53`; SVar = `AF21 + non-AF32`; real non-AF parents `33`; unresolved `0`.

### Direct-G 28

- behavior run `33516084949`; artifact `9803814288`; digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`; 28/28 Record/Replay PASS.
- Principal Observation v4 run `33552816460`; artifact `9818304005`; hidden/observation gates PASS.
- requirement artifact `9822685407`; digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`; ABI v2.1 + 17/17 negatives PASS.

### AF21

- Runtime v2 run `33773548765` PASS.
- ABI/Decision/RNG/Replay v2 run `33773805031` PASS.
- Principal Observation v5 run `33774853355`; artifact `9901438964`; digest `sha256:2e60f7c79ad642f3f3942db4b3e84a9392cde5662126c0eb84153a3f0469cb5d`; PASS.

## Current G3 frontier

- total G3 `81`
- immutable Direct-G `28`
- immutable AF `21`
- remaining effective paths `32`
- remaining production parents `33`
- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`

## Non-AF attempt chain

1. `33797779388`: manifest-file hash vs consumer-model hash confusion; repaired.
2. `33798342466`: pinned MagicStack declaration anchor mismatch; repaired.
3. `33798608932`: ChangesZone fixture enum/string mismatch; repaired with `.name()`.
4. `33816948410`: first parent `1/1/0`; common non-resolution exposed.
5. `33817799382`: lineage Event request-trace ABI gap; repaired.
6. `33818067742`: diagnostic `TreeMap` compile failure; repaired.
7. `33818428322`: `resolutionCallbacks=0`; matcher false-negative excluded.
8. `33819960784`: lifecycle overlay applies; harness not yet consuming it.
9. `33820366293`: first parent never enters `MagicStack.add`; fizzle/stack-target rejection excluded.
10. `33820842986`: first common rejection `OPTIONAL_COST_SELECTION_NULL` before `playAbility(...)`.
11. `33851809027`: singleton repair succeeds; next blocker principal-scoped hidden observation.
12. `33853430763`: INVALID pre-runtime run from accidental source-pin truncation; excluded.
13. `33853539153`: qualified observation/lifetime stack PASS, record Step 14 PASS; strict Step 15 leaves 8 event-shape/admission failures.

## Exact next atomic package

1. Repair the two directly proven generic event-fixture defects only:
   - establish `Phase` target state before `resetActiveTriggers()`;
   - make `AttackersDeclared.AttackedTarget` the same aggregate Iterable shape as pinned production.
2. Add observation-only diagnostics for the remaining expected `Study Hall / TriggersWhenSpent` trigger rejection if the exact `canRunTrigger` gate cannot be derived without guessing. Do not alter trigger legality.
3. Persist the repair/telemetry source commit, allow exactly one successor event-runtime run, and immediately checkpoint run/job/source HEAD/TREE.
4. Terminally adjudicate. If Study Hall remains the first/only failure, freeze the exact rejection evidence before repair.
5. Continue until strict non-AF Runtime PASS for all 32 effective paths / 33 parents and required Decision22/RNG10 obligations.
6. Freeze Runtime PASS, then perform a separate immutable ABI/Decision/RNG/Replay certification consuming the exact runtime artifact; then perform non-AF Principal Observation Hidden31 record/replay equivalence with no leaks.
7. Only after Direct28 + AF21 + non-AF32 satisfy all contracts may G3 be promoted/frozen and serial closure proceed `ABC -> D -> E -> F`.

Control expectations remain non-authoritative until fresh successor computation: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
