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

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_RUN_33819960784_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33819960784_FAILURE.md`

Run `33819960784` / job `100860290828` is terminal `failure`. The lifecycle-enhanced Forge overlay applies, compiles and executes the full record campaign without changing the prior first-parent outcome. Because the harness at this source did not register the new lifecycle observer, the artifact intentionally contains no parent-correlated stack-lifecycle evidence. The next authorized change is only the harness-side consumer for the already-present observation-only lifecycle callback.

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

### Attempt 5 — diagnostic request-trace ABI failure

- source HEAD `4c97b95ea3777f20ed2239f8a38aae82b2abc217`
- source TREE `413096e4ba7bbb131edc31ebaf7534b519647fd3`
- run `33817799382`, job `100853681886`
- artifact `9917183980`
- digest `sha256:9b15ab387e0bb920e800e38d13d96030bbd7371b05b93ff7e9919ceaf79051ac`
- steps 1–11 PASS; step 12 FAIL; runtime/replay NOT RUN; evidence upload PASS.
- cause: request-trace `replace_one_of` did not support the lineage-enhanced Event write chain.
- repair commit `8446cfc72060156db63237cb7c4b00045ef72fbb` added one exact lineage Event ABI while keeping ambiguity fail-closed.

### Attempt 6 — diagnostic Java compile failure

- source HEAD `8446cfc72060156db63237cb7c4b00045ef72fbb`
- source TREE `f625b3cbaf0825bc17934e667858adf2defbec57`
- run `33818067742`, job `100854474552`
- artifact `9917297622`
- digest `sha256:34a0f2185d19d19724b7e1d3c7dcffc0d1da764f6d4c5180f2bf2622aee806ea`
- steps 1–13 PASS; step 14 failed during Maven `testCompile`; test body NOT EXECUTED.
- cause: observation-only `mapHash` helper referenced unqualified `TreeMap` without inherited import.
- compile repair commit `3e2260fe7b8a1a7a1d9fea932301b6fac3b3b3c6` changed only the diagnostic helper to `java.util.TreeMap`.

### Attempt 7 — terminal lineage runtime evidence

- source HEAD `3e2260fe7b8a1a7a1d9fea932301b6fac3b3b3c6`
- source TREE `5f757dc8bc0c85fdea10d6e0cc8da762865e23a7`
- run `33818428322`, job `100855531128`
- artifact `9917438334`
- digest `sha256:696556a4e4163308ec00ef123b691a9eaa73e6742058220ac1041d73cef7fa6f`
- steps 1–14 PASS; Step 15 FAIL; replay/source-chain NOT RUN; evidence upload PASS.
- first parent `Ingenious Smith/ChangesZone/TrigDig`: admissions `1`, bindings `1`, executions `0`, resolutionCallbacks `0`.
- admitted target identity: ability `225`, sourceTrigger `50001`, host `96`, API `Dig`; original/current map fingerprints equal.
- this directly rejects post-fizzle matcher false-negative for first parent and narrows the shared boundary to real-stack placement versus pre-observer fizzle.

### Attempt 8 — lifecycle overlay-only reproduction

- source HEAD `8cc9085267174fa08ec44998dba75384638f70a0`
- source TREE `46cd9b9d4f06fc1b485ae1d137e44cb5de5c85d7`
- run `33819960784`, job `100860290828`
- artifact `9917974166`
- digest `sha256:88dbd82d6db6318517176497ade0713fd53454e236f7e381e76d79a5f4bfe97e`
- downloaded ZIP re-hash matched exactly.
- steps 1–14 PASS; Step 15 FAIL; replay/source-chain NOT RUN; evidence upload PASS.
- first parent remains `1/1/0` with resolutionCallbacks `0`.
- Forge overlay now exposes observation-only stages `ADD_ENTER`, `ADD_TARGET_REJECT`, `FROZEN_QUEUE`, `STACK_PUSH`, and `FIZZLE_RESULT` and still exposes post-fizzle pre-resolution callback.
- harness at this source did not register the lifecycle observer, so no `stack-lifecycle.tsv` exists. This run proves overlay applicability and semantically neutral reproduction only; it does not resolve the placement/fizzle distinction.

## Exact next atomic package

1. Extend the already-invoked harness instrumentation so the lineage Event harness registers `MagicStack.setWs33StackLifecycleObserver` and records parent-correlated lifecycle rows.
2. For each lifecycle callback record at least parent key, stage, boolean flag, wrapper state, effective ability ID, source-trigger ID, host ID, API, original/current map fingerprints, strict target-match observation, and admitted ability/source-trigger/host identity.
3. Materialize `stack-lifecycle.tsv` in record/replay evidence and clear the observer during cleanup.
4. Do not change `matchesTarget`, `targetExecutions`, TriggerHandler legality, target choices, MagicStack ordering, fizzle semantics, event fixtures, Decision/RNG/request semantics, or coverage.
5. Commit only the harness-consumer instrumentation.
6. Allow exactly one `ws33-g3-svar-event-runtime.yml` successor run and immediately persist run/job/source HEAD/TREE.
7. Terminally adjudicate that artifact:
   - no `ADD_ENTER` for admitted target => production `PlaySpellAbility` fails before MagicStack.add; instrument/inspect its exact prerequisite next;
   - `ADD_ENTER` but no `STACK_PUSH`, with target rejection/frozen evidence => classify exact add-stage cause;
   - `STACK_PUSH` plus `FIZZLE_RESULT=true` => inspect exact fizzle cause;
   - `STACK_PUSH` plus `FIZZLE_RESULT=false` but no existing resolution callback => observer defect.
8. Freeze a failure checkpoint and update this handoff before any repair/retry.
9. Continue until Runtime strict PASS; then freeze Runtime before separate ABI/Decision/RNG/Replay certification and Principal Observation/Hidden31 qualification.
10. Only after Direct28 + AF21 + non-AF32 satisfy all behavior/decision/RNG/replay/hidden/provenance/fail-closed contracts may G3 be promoted/frozen and serial closure proceed to `ABC -> D -> E -> F`.

Control expectations remain non-authoritative until fresh successor computation: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
