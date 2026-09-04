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

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_RUN_33854808213_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33854808213_FAILURE.md`

Run `33854808213` / job `100965530844` is terminal `failure`.

- source HEAD `99377107cf860876bd5ee43fbc8121802ad9336e`
- source TREE `515c9847f54fd4eeb1a3375a36913a6cc990d274`
- artifact `9929834690`
- digest `sha256:86c85663680643b6fba00ebc0450df15d9d192b6d8d36f13f74ed494b9a51d82`
- downloaded ZIP re-hash: exact match
- source/topology/pins/overlays/harness PASS
- Step 14 record campaign PASS
- Step 15 strict adjudication FAIL
- replay/source-chain skipped
- evidence upload PASS
- coverage promotion FALSE

### Attempt-14 material result

The generic Phase-registration and AttackersDeclared runParam-shape repairs are confirmed without regression:

- all 5 formerly failing Phase parents PASS;
- both formerly failing AttackersDeclared parents PASS;
- strict parent partition is now `32 PASS / 1 FAIL` of 33;
- strict effective-path partition is now `31 PASS / 1 FAIL` of 32.

No partial result is promoted.

The sole remaining runtime blocker is:

`forge-behavior-v2:ae82d4423a23aaf18b7da0e9215165e8d55ba5f2#1`

- card `Study Hall`
- source directive `SVAR`
- parent SVar `TrigSpent`
- mode `SpellCast`
- target SVar `TrigScry`
- dispatch `Scry`
- admission/binding/execution `0/0/0`
- failure `source-proven trigger admission count=0`

The harness reaches this parent through the actual source mana ability's `AbilityManaPart.addTriggersWhenSpent(spell)` and actual `MagicStack.addAndUnfreeze(spell)` path. The exact rejection gate inside the delayed-trigger / `canRunTrigger` path is still UNKNOWN. Do not repair Study Hall or `TriggersWhenSpent` by card name or inference.

## Frozen system repairs already validated

### Non-discretionary singleton trigger-play selection

Pinned Forge singleton additional-cost variants are non-discretionary. The repair returns only `abilities.get(0)` when `size()==1`; empty/multi-option paths preserve the existing fail-closed/external path. Attempt 11 proved the former Ingenious Smith blocker advances to `1/1/1`.

### Principal-scoped hidden-card observation/lifetime

Non-AF runtime reuses the qualified Direct-G/AF stack:

1. `apply-ws33-observation-fanout.py`
2. `apply-ws33-external-card-decision-lifetime.py`

Both PASS in the current runtime lineage with zero rules mutation and zero pilot fallback.

### Generic event-fixture alignment

- Phase target state is established before `resetActiveTriggers()`, matching pinned Forge's `isTriggerActive()->phasesCheck(game)` registration semantics.
- `AttackersDeclared.AttackedTarget` uses an aggregate Iterable shape matching pinned `PhaseHandler` / `TriggerAttackersDeclared`.
- Run `33854808213` validates all seven formerly affected parents.

## Invalid run excluded

Run `33853430763` / job `100961180376` is permanently `INVALID / NOT QUALIFICATION EVIDENCE` because an intermediate workflow rewrite truncated `DIRECT_RUNTIME_SOURCE_HEAD`. The exact pin was restored before eligible successors.

## G3 immutable evidence — do not rerun without invalidation

### Topology

- run `33681121017` SUCCESS; job `100417671589`; artifact `9866293827`; digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`.
- partition `G81 = Direct28 + SVar53`; SVar = `AF21 + non-AF32`; real non-AF parents `33`; unresolved `0`.

### Direct-G 28

- behavior run `33516084949`; artifact `9803814288`; digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`; 28/28 Record/Replay PASS.
- Principal Observation v4 run `33552816460`; artifact `9818304005`; hidden/observation gates PASS.
- requirement artifact `9822685407`; ABI v2.1 + 17/17 negatives PASS.

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
- latest record materially green: 31/32 paths and 32/33 parents, not promoted
- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`

## Non-AF attempt chain

1. `33797779388`: manifest-file vs consumer-model hash confusion; repaired.
2. `33798342466`: MagicStack declaration anchor mismatch; repaired.
3. `33798608932`: ChangesZone enum/string fixture mismatch; repaired.
4. `33816948410`: common `1/1/0` non-resolution exposed.
5. `33817799382`: lineage request-trace ABI gap; repaired.
6. `33818067742`: diagnostic TreeMap compile failure; repaired.
7. `33818428322`: zero resolution callbacks confirmed.
8. `33819960784`: lifecycle overlay applies; harness consumer gap.
9. `33820366293`: trigger never enters MagicStack.add.
10. `33820842986`: `OPTIONAL_COST_SELECTION_NULL` isolated.
11. `33851809027`: singleton repair PASS for prior blocker; hidden observation becomes next blocker.
12. `33853430763`: INVALID pre-runtime pin typo; excluded.
13. `33853539153`: observation/lifetime stack PASS; 25/33 parents PASS, 24/32 paths PASS; Phase/Attackers defects isolated.
14. `33854808213`: Phase + Attackers fixes confirmed; 32/33 parents PASS, 31/32 paths PASS; Study Hall isolated.

## Exact next atomic package

1. Add observation-only trigger-gate telemetry for the expected Study Hall delayed trigger. It must preserve every existing boolean result and record only rejection stage / opaque identity metadata.
2. Cover both `isTriggerActive` and `canRunTrigger` gates because delayed triggers pass through both before `runSingleTrigger`.
3. Match the expected delayed trigger generically by source-card id + spawning-ability identity + exact original parent map; no card-name production branch.
4. Emit immutable per-parent gate evidence and keep all existing 33-parent/32-path gates unchanged.
5. Commit the instrumentation atomically so it produces one diagnostic successor run, then immediately persist source HEAD/TREE/RUN/JOB.
6. Terminally adjudicate the exact Study Hall rejection stage. Persist it before any repair.
7. Repair only the proven systemic cause; then continue until strict non-AF Runtime PASS for all 32 paths / 33 parents plus required Decision22/RNG10 obligations and replay.
8. Freeze Runtime PASS, then perform separate immutable ABI/Decision/RNG/Replay certification consuming that exact artifact, then non-AF Principal Observation Hidden31 record/replay equivalence with no leaks.
9. Only after Direct28 + AF21 + non-AF32 satisfy all contracts may G3 be promoted/frozen and serial closure proceed `ABC -> D -> E -> F`.

Control expectations remain non-authoritative until fresh successor computation: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
