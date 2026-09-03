# WS33 CONTINUATION HANDOFF

## Stable checkpoint

Branch: `work/ws33-integrated-closure-20260831`

The operative WS33 state is artifact-driven. The repository-root WS33 JSON files are tooling/reference inputs and are **not** the current 4188-path operational successor. Do not attempt to canonicalize the operational state by copying artifact files into the branch root.

### Formal frontier

- effective: `4188`
- PASS: `285`
- UNKNOWN: `3903`
- FAIL: `0`
- UNSUPPORTED: `0`
- G UNKNOWN: `81`
- H UNKNOWN: `0`

### Direct-G behavior — immutable PASS

- run: `33516084949`
- source HEAD: `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`
- source TREE: `857dc01e04f58ca59437e08710bcb194bf030ea4`
- artifact: `9803814288`
- digest: `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`
- 28/28 Record PASS
- 28/28 tape-driven Replay PASS
- strict failures: `0`
- stack admission/resolution: PASS
- hidden leaks: `0`
- cross-principal leaks: `0`
- semantic replay: PASS

Do not rerun this campaign merely for reassurance. A supplemental execution is allowed only to capture evidence fields required by the current ABI that the immutable artifact did not retain.

### Direct-G principal observation v4 — immutable PASS

- run: `33552816460`
- artifact: `9818304005`
- strict source-profile adjudication: PASS
- expected paths: `28`
- hidden-required paths: `24`
- record observation events: `1496`
- replay observation events: `1496`
- unauthorized/private leak delta: `0`
- cross-principal leak delta: `0`
- principal transport: `REMOTE_CLIENT_DELTA`

### G evidence-requirement migration — immutable PASS

Qualified errata:

- run: `33564749471`
- artifact: `9822685407`
- digest: `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`
- corrected G paths: `60`
- existing PASS requirement profiles changed: `0`
- revalidated PASS paths: `285`
- coverage mutated: `false`
- source-proven G requirements: Hidden `74`, RNG `21`, Replay `57`, Decision `50`
- successor effective-model SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- ABI V2.1 gate: PASS
- 17 negative ABI fixtures: rejected for intended reason
- `ws33_verify.py`: PASS

Operational successor freeze:

- run: `33566624518`
- source HEAD: `c5d6cb8f4831e61b4ee8a1176ccbe4f6b98479ea`
- artifact: `9823383539`
- digest: `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`
- effective: `4188`
- PASS: `285`
- UNKNOWN: `3903`
- G UNKNOWN: `81`
- model SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`

This artifact is the current qualified operational predecessor for Direct-G promotion.

## Current G3 recovery checkpoint — 2026-09-03

`LAST_CONFIRMED_CHECKPOINT = G3_SVAR_AF_CHOICE_REPAIR_VALIDATION_RUNNING`

Current branch: `work/ws33-g3-final-closure-20260902`

Last fully adjudicated runtime HEAD before the current repair:

- HEAD: `9fd0f74782e18fb9202b698011b4653de17244f4`
- TREE: `632ff95d625e5cdfcdafb815e7b958c16d923aff`
- commit: `ws33 g3: align AF case loader with 19-field identity ABI`

### Already closed in G3 — do not repeat

- principal-scoped DecisionEvent identity defect repaired and hardened with negative fixtures;
- hardened ABI run `33690697036`, artifact `9870061705`, digest `sha256:21bfde999292f5d3a3d1cc5f27e5236ab352972cedde7b32691ea5ad31fbe0cd` PASS;
- 53-SVar consumer topology run `33681121017`, artifact `9866293827`, digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b` PASS, unresolved parents `0`;
- topology hash-space mismatch in the AF workflow corrected: `MODEL_FILE_SHA=cd48f4...` is distinct from embedded `CONSUMER_MODEL_SHA=82638e...`;
- AF parent construction repaired to preserve actual-card root/named-parent-SVar identity instead of detached script-only reconstruction;
- target-SVar reachability observer added at `AbilitySub.resolve()` as observation-only evidence;
- 19-field AF case ABI loader aligned.

### Latest fully adjudicated AF runtime evidence

Run: `33733426616`

Job: `100578369590`

Artifact: `9884893619`

Digest: `sha256:1202fbcdd1c2f77100e3a061aff84ec2738715b54313ad29978a59b141f4987f`

Direct artifact adjudication:

- Maven / Forge test execution: `BUILD SUCCESS`;
- case rows: `21/21 PASS`;
- stack admissions: `21/21`;
- stack resolutions: `21/21`;
- target-SVar reachability: `17/21`;
- workflow is correctly red because qualification requires target-SVar reachability for every AF path;
- this run is diagnostic only and MUST NOT be promoted.

The four exact paths with `targetExecutions=0` are:

1. `forge-behavior-v2:95726bbbfdb31ba1e8fe7146f4a7971d93f97bc5a` — Ao, the Dawn Sky — `Charm -> TrigDig -> DigEffect`;
2. `forge-behavior-v2:a1fe7a20bc3ddb26ed8642a7a8b5025697bd0d83` — Atsushi, the Blazing Sky — `Charm -> ExileTwo -> DigEffect`;
3. `forge-behavior-v2:b028d2d29f150fd3ff7bcbc30706f5d4e2282907` — Kindred Summons — `ChooseType -> DBDigUntil -> DigUntilEffect`;
4. `forge-behavior-v2:ee17650cc69e7d571ba8a6d602227eb4c8ba6154` — Prismari Charm — `Charm -> DBSurveil -> SurveilEffect`.

### Root-cause adjudication for the four gaps

`CODE_DERIVED` against pinned Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`:

- `CharmEffect.makeChoices(sa)` is the production phase that selects and chains `Choices$` modes before stack resolution; `SpellAbility.setupTargets()` alone does not perform that step. The current AF harness admits Charm parents directly to `MagicStack`, so their modeled mode is never guaranteed to be chained. This explains the three Charm gaps without implying a Forge Dig/Surveil rules defect.
- `ChooseTypeEffect.resolve()` performs an authoritative discretionary creature-type choice. `Kindred Summons` only reaches `DBDigUntil` when `X > 0`; the current generic pilot may select a legal type that the actor controls zero of. This is a reachability-fixture/pilot-selection issue, not a `DigUntilEffect` rules failure.
- retained decision requests prove the Kindred Summons choice is externalized as principal-scoped `GUI_ONE` with `350` authoritative options; no prompt parsing or legality synthesis is required.
- retained decision requests contain no `MODE_SELECTION` for the three failing Charm paths, independently confirming that the production Charm mode-preparation phase was absent from the prior harness route.

### Current atomic repair — PARTIAL pending CI adjudication

Persistent repair commit:

- HEAD: `5d1fa3a55e41f2a99c31c49f177b9ca98fe17592`
- TREE: `0fc720f45246030546c1eda995f2d6729d16d04e`
- commit: `ws33 g3: drive AF parent choices through Forge`
- changed file: `ws33_prepare_g_svar_af_harness.py`

Repair semantics:

- modal `Charm` parents call Forge production `CharmEffect.makeChoices(sa)` before `setupTargets()` and MagicStack admission;
- the qualification pilot chooses the source-proven mode ordinal only from the authoritative `MODE_SELECTION` option list;
- `ChooseType` reachability selects semantic value `Bear` only if `Bear` is present in the authoritative actor-scoped `GUI_ONE` options; otherwise it throws `UNSUPPORTED_DECISION_PATH` fail-closed;
- no card-name branch, no direct target-SVar entry, no direct `sa.resolve()`, no manual target injection, no synthetic legal options.

Focused validation:

- run: `33742586083`
- job: `100607668592`
- exact head: `5d1fa3a55e41f2a99c31c49f177b9ca98fe17592`
- state at checkpoint: `IN_PROGRESS`
- completed gates so far: checkout tooling PASS; frozen topology download/validation PASS; pinned Forge/dependency checkout in progress.

If execution is interrupted, inspect this exact run first. Do not rerun or modify the repair until its job result and retained artifact are adjudicated.

### Exactly next work package

1. Adjudicate run `33742586083` and its retained artifact.
2. If green at the runtime gate, require `21/21 PASS`, stack admission/resolution `21/21`, exact target-SVar reachability `21/21`, then adjudicate hidden/RNG/decision/replay obligations before promotion.
3. If red, isolate only the first new root cause from the exact run/artifact and repair it systemically.
4. Persist the run/job/artifact/digest and adjudication here before beginning the 32-path non-AF event campaign.

## Subsequent serial queue

After AF closure, qualify the 32 non-AF G SVar paths through source-proven production parent/event entrypoints. Then G3 may be promoted only at `G=81/81 PASS` with all evidence obligations satisfied. Only after freezing the exact G3 successor may the serial campaigns proceed `ABC -> D -> E -> F`.

Expected control counts are not source truth until freshly computed from each successor:

- post-G3: PASS `366`, UNKNOWN `3822`;
- post-ABC: PASS `1920`, UNKNOWN `2268`;
- post-D: PASS `2840`, UNKNOWN `1348`;
- post-E: PASS `3869`, UNKNOWN `319`;
- post-F: PASS `4188`, UNKNOWN `0`.

## Completion state

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

No timeout, context switch, or green workflow may change these flags without the full final 4188-path qualification and required cross-gates.
