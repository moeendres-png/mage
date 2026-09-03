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

`LAST_CONFIRMED_CHECKPOINT = G3_SVAR_AF_PATH_SPEC_SCOPE_FIX_VALIDATION_RUNNING`

Current branch: `work/ws33-g3-final-closure-20260902`

Last fully adjudicated behavior-bearing AF runtime HEAD:

- HEAD: `9fd0f74782e18fb9202b698011b4653de17244f4`
- TREE: `632ff95d625e5cdfcdafb815e7b958c16d923aff`
- run: `33733426616`
- artifact: `9884893619`
- digest: `sha256:1202fbcdd1c2f77100e3a061aff84ec2738715b54313ad29978a59b141f4987f`
- behavior rows: `21/21 PASS`
- stack admission/resolution: `21/21`
- target-SVar reachability: `17/21`
- diagnostic only; not promotable.

### Already closed in G3 — do not repeat

- principal-scoped DecisionEvent identity defect repaired and hardened with negative fixtures;
- hardened ABI run `33690697036`, artifact `9870061705`, digest `sha256:21bfde999292f5d3a3d1cc5f27e5236ab352972cedde7b32691ea5ad31fbe0cd` PASS;
- 53-SVar consumer topology run `33681121017`, artifact `9866293827`, digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b` PASS, unresolved parents `0`;
- topology hash-space mismatch in the AF workflow corrected: `MODEL_FILE_SHA=cd48f4...` is distinct from embedded `CONSUMER_MODEL_SHA=82638e...`;
- AF parent construction repaired to preserve actual-card root/named-parent-SVar identity instead of detached script-only reconstruction;
- target-SVar reachability observer added at `AbilitySub.resolve()` as observation-only evidence;
- 19-field AF case ABI loader aligned.

### Four previously unreached target SVar paths

1. `forge-behavior-v2:95726bbbfdb31ba1e8fe7146f4a7971d93f97bc5a` — Ao, the Dawn Sky — `Charm -> TrigDig -> DigEffect`;
2. `forge-behavior-v2:a1fe7a20bc3ddb26ed8642a7a8b5025697bd0d83` — Atsushi, the Blazing Sky — `Charm -> ExileTwo -> DigEffect`;
3. `forge-behavior-v2:b028d2d29f150fd3ff7bcbc30706f5d4e2282907` — Kindred Summons — `ChooseType -> DBDigUntil -> DigUntilEffect`;
4. `forge-behavior-v2:ee17650cc69e7d571ba8a6d602227eb4c8ba6154` — Prismari Charm — `Charm -> DBSurveil -> SurveilEffect`.

`CODE_DERIVED` root causes remain:

- Charm parents require production `CharmEffect.makeChoices(sa)` before target setup/stack admission; prior direct MagicStack harness route omitted that phase.
- Kindred Summons requires an authoritative creature-type choice represented by controlled fixture creatures; retained request evidence exposes the choice as principal-scoped `GUI_ONE` with 350 authoritative options.

### Choice repair attempt `5d1fa3a...` — COMPILE_FAILED

Persistent code commit:

- HEAD: `5d1fa3a55e41f2a99c31c49f177b9ca98fe17592`
- TREE: `0fc720f45246030546c1eda995f2d6729d16d04e`
- run: `33742586083`
- job: `100607668592`
- artifact: `9888407854`
- digest: `sha256:1c27ae7659c33c479042d07b918be70241d20ea09b7b656ea0dca10317fb34de`

Artifact adjudication:

- topology/pins/overlay/harness-preparation: PASS;
- Maven fails at Java test compilation before any of the 21 cases execute;
- exact compiler error: generated `Ws33GSVarAfQualificationTest.java` references variable `evidence` inside static `selectByPathPolicy`, but `evidence` is local to the campaign test method;
- therefore this run carries **no new behavior evidence** and does not invalidate the prior 21/21 behavior / 17/21 reachability diagnostic;
- classification: `FAILED` harness-scope defect, not Forge rules/runtime failure.

### Current atomic repair — PARTIAL pending CI adjudication

Persistent scope-fix commit:

- HEAD: `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`
- TREE: `0fa6dd43fff0176037f97a5d5f79789b61e029ac`
- commit: `ws33 g3: scope AF path specs for external pilot`
- changed file: `ws33_prepare_g_svar_af_harness.py`

Repair semantics:

- adds a test-only static path→`CaseSpec` registry populated from the already authoritative 21 case inputs at campaign entry;
- the External-Decision policy reads only this case identity registry, never the local behavior-evidence map;
- registry is cleared in test cleanup to preserve process isolation;
- Charm production mode preparation and authoritative option-only type/mode choices are otherwise unchanged;
- no card-name branch, no direct target-SVar entry, no direct `sa.resolve()`, no manual target injection, no synthetic legal options.

Focused validation:

- run: `33743144684`
- exact head: `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`
- state at checkpoint: `IN_PROGRESS`

If execution is interrupted, inspect run `33743144684` first. Do not modify or rerun the repair until its exact job result and retained artifact are adjudicated.

### Exactly next work package

1. Adjudicate run `33743144684` and retained artifact.
2. If compilation/runtime gate is green, require `21/21 PASS`, stack admission/resolution `21/21`, target-SVar reachability `21/21`.
3. Then separately adjudicate all source-required hidden/RNG/decision/replay obligations before any AF promotion; the focused record-only runtime gate is not by itself qualification-complete.
4. If red, isolate only the first new root cause from this exact run/artifact, repair systemically, and checkpoint before continuing.
5. Only after AF evidence completion begin the 32-path non-AF event campaign.

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
