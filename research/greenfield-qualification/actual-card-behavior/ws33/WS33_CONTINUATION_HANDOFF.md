# WS33 CONTINUATION HANDOFF

## Completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

The operative state is artifact/checkpoint-driven. Historical root/current JSON names are not automatically current closure truth.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

Only the final serial `G3 -> ABC -> D -> E -> F` successor with all 4188 effective paths PASS, zero UNKNOWN/FAIL/UNSUPPORTED, A-H UNKNOWN zero, exact pin/model/lineage, and all replay/hidden/RNG/decision/failure/evidence/hash gates may change these flags.

## Stable predecessor

- effective `4188`; PASS `285`; UNKNOWN `3903`; FAIL `0`; UNSUPPORTED `0`; G UNKNOWN `81`; H UNKNOWN `0`.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- effective-manifest file SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- predecessor artifact `9823383539`, digest `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`.

## Current confirmed checkpoint

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_RUN_33817799382_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33817799382_FAILURE.md`

Run `33817799382` / job `100853681886` is terminal `failure` before Runtime. The diagnostic event-harness transform itself passed, but the authoritative-request instrumentation rejected the new observation-only write chain because its exact Event ABI did not yet include `writeResolutionLineage(outDir)`. No Java campaign ran, so the previously frozen first-parent `1/1/0` reachability question remains unresolved. The next authorized change is only the narrow request-trace ABI repair described below.

## G3 immutable evidence — do not rerun for reassurance

### Topology

- run `33681121017` SUCCESS
- job `100417671589` SUCCESS
- source HEAD `4032d9c14dc7840e2518a92273037aaba443ada9`
- source TREE `d86b141171397d8a3d59c556f45b27f8cc6268d9`
- artifact `9866293827`
- digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`
- schema `commander-simulator-next.ws33-g-svar-consumer-topology.v2`
- topology consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`
- partition: `G81 = Direct28 + SVar53`, unresolved parents `0`; SVar = `AF21 + non-AF32`; non-AF = `33` real source-proven production parent entrypoints.

Important hash distinction: topology v2's `effective_model_sha256` is the effective manifest's `consumer_model_sha256`; it is not the SHA256 of `WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json`. Do not equate `82638e...` with the manifest-file SHA `cd48f427...`.

### Direct-G 28

Behavior run `33516084949` / artifact `9803814288` / digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`: `28/28` Record/Replay PASS.

Principal Observation v4 run `33552816460` / artifact `9818304005` / digest `sha256:7b39edd3cd67f1e0b398db90fbb592b7786372fe5b398b1a0bed39e79d24bbfc`: principal-scoped observation/hidden gates PASS.

Requirement artifact `9822685407`, digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`, remains the successfully generated-and-strictly-verified requirement evidence. Its parent workflow later failed during branch materialization and is not reclassified as a workflow PASS.

### AF21

AF is qualification-complete through focused immutable gates:

- Runtime v2 run `33773548765` PASS.
- ABI/Decision/RNG/Replay v2 run `33773805031` PASS.
- Principal Observation v5 run `33774853355` PASS; job `100713875152`; artifact `9901438964`; digest `sha256:2e60f7c79ad642f3f3942db4b3e84a9392cde5662126c0eb84153a3f0469cb5d`.

Do not rerun these without a concrete invalidating code/pin/contract change.

## Current G3 frontier

- total G3: `81`
- immutable Direct-G qualified: `28`
- immutable AF qualified: `21`
- remaining effective paths: `32`
- remaining production parent entrypoints: `33`
- global G3 coverage promotion: `FALSE`

Remaining production-parent modes: ChangesZone `12`, Phase `6`, Attacks `5`, DamageDone `4`, SpellCast `2`, AttackersDeclared `2`, DamageDoneOnce `1`, Sacrificed `1`.

Invariant: Kang Prime retains both real source-proven parent entrypoints.

## Non-AF runtime attempts

### Attempt 1 — adjudicated

- source `0b1afc7be70f5a74b38516e3848f526f3693eac4`
- run `33797779388`, job `100789526018`, failure before runtime
- cause: topology consumer-model hash `82638e...` was incorrectly compared to manifest-file hash `cd48f...`.

### Attempt 2 — adjudicated

- source `935da1abf48b84f85e4265a26ba65fb546e8cb07`
- run `33798342466`, job `100791376533`, partial artifact `9910100377`
- digest `sha256:ced3f9f26efe6f0540b4d8b661f5afad0fea2adc5071762866864658d1fb846a`
- cause: observation-only MagicStack overlay used a class-declaration anchor that omitted pinned Forge's literal `/* extends MyObservable */` comment.

### Attempt 3 — adjudicated and repaired

- source HEAD `26ec46d852a731054e8719e5bf1ea37bef3f6ea6`
- source TREE `793c1e3c10cf07f4d0b432a56aa0f90e73eb7fe0`
- run `33798608932`, job `100792262743`
- artifact `9910414457`
- digest `sha256:796d734fe0f3074319d4471e691ce356f4fe16d7661f8aee5223d48f1cf521c1`
- Step 14 PASS; Step 15 FAIL; replay NOT RUN; coverage promotion FALSE.
- first parent `Ingenious Smith/ChangesZone` = `0/0/0` admission/binding/execution.
- confirmed cause: event fixture supplied `ZoneType` enums where pinned production `GameAction.changeZone` supplies zone-name Strings.
- narrow repair commit `3bf09bc325ee5094d2a4874bbc133520f5f759dc` changed only `AbilityKey.Origin/Destination` to `.name()` values.

### Attempt 4 — terminal runtime evidence

- source HEAD `3bf09bc325ee5094d2a4874bbc133520f5f759dc`
- source TREE `8e0a65344e4257fa51e2b15dfdac35e4883bd9ae`
- run `33816948410`, job `100851076967`
- artifact `9916940071`
- digest `sha256:4e1ed01602e46b796bdcd257964e9fc56d32aa370112c94cc57c64d8ef8b0871`
- Step 14 PASS; Step 15 FAIL; replay NOT RUN; coverage promotion FALSE.
- first parent `forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1` (`Ingenious Smith`, `ChangesZone`) = admission/binding/execution `1/1/0`.
- artifact-wide: 33 parents; one `1/1/1` PASS (`Descendants' Fury`); 24 failures at `1/1/0`; eight later event-specific failures.
- unresolved distinction: actual production stack/non-resolution versus false-negative resolution identity measurement.

### Attempt 5 — observation-only diagnostic failed pre-runtime

- diagnostic source HEAD `4c97b95ea3777f20ed2239f8a38aae82b2abc217`
- source TREE `413096e4ba7bbb131edc31ebaf7534b519647fd3`
- run `33817799382`, job `100853681886`
- artifact `9917183980`
- digest `sha256:9b15ab387e0bb920e800e38d13d96030bbd7371b05b93ff7e9919ceaf79051ac`
- artifact ZIP re-hash matched exactly
- steps 1–11 PASS
- step 12 `Prepare 33-parent event harness with request trace` FAIL
- record/runtime/replay NOT RUN
- evidence upload PASS
- coverage promotion FALSE

Artifact `diagnostic/event-harness.log` proves the lineage-enhanced Event transform passed. The request-trace patch then failed because its `replace_one_of` supports Direct ABI and pre-lineage Event ABI only. The generated chain now contains `writeParentEvidence(outDir);writeResolutionLineage(outDir);...`, so both old anchors count zero. Exact source-derived failure and repair scope are frozen in `G3_NON_AF_EVENT_RUNTIME_RUN_33817799382_FAILURE.md`.

## Exact next atomic package

1. Extend `ws33_instrument_g_authoritative_requests.py` with a third exact Event ABI matching the lineage-enhanced write chain. Preserve Direct and pre-lineage Event support and preserve `replace_one_of` ambiguity rejection.
2. The lineage Event replacement must insert `writeWs33DecisionRequests(outDir)` after `writeResolutionLineage(outDir)` and before controller-factory cleanup.
3. Do not change `matchesTarget`, `targetExecutions`, lineage fields, event fixtures, Forge overlays, Decision/RNG semantics, or coverage.
4. Commit only that request-trace ABI repair.
5. Allow exactly one `ws33-g3-svar-event-runtime.yml` retry from it and immediately persist run/job/source HEAD/TREE.
6. Terminally adjudicate its artifact. Only a runtime artifact containing `resolution-lineage.tsv` may resolve the first-parent `1/1/0` distinction.
7. If `resolutionCallbacks > 0` while `targetExecutions == 0`, compare admitted/resolving IDs/source-trigger/host/API/map fingerprints and repair only the confirmed measurement identity defect. If callbacks are zero, investigate actual production stack/non-resolution instead.
8. Continue strict failure-checkpoint -> repair -> single-run discipline until Runtime PASS, then freeze Runtime before separate ABI/Decision/RNG/Replay certification and Principal Observation/Hidden31 qualification.
9. Only after Direct28 + AF21 + non-AF32 satisfy all required contracts may G3 be promoted/frozen and serial closure proceed to `ABC -> D -> E -> F`.

Control expectations are non-authoritative until fresh successor computation: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
