# WS33 CONTINUATION HANDOFF

## Completion contract

Active branch: `work/ws33-g3-final-closure-20260902`.

The operative WS33 state is artifact-driven. Repository-root WS33 JSON files are tooling/reference inputs, not the current 4188-path successor.

`TASK_COMPLETE = NO`

`WS33_COMPLETE = FALSE`

Only the final serial `G3 -> ABC -> D -> E -> F` successor with all 4188 effective paths PASS, zero UNKNOWN/FAIL/UNSUPPORTED, A-H UNKNOWN zero, exact pin/model/lineage, and all semantic-replay/hidden/RNG/decision/failure/evidence/hash gates may change these flags.

## Stable operational predecessor

- effective `4188`; PASS `285`; UNKNOWN `3903`; FAIL `0`; UNSUPPORTED `0`; G UNKNOWN `81`; H UNKNOWN `0`.
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- model SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.
- predecessor artifact `9823383539`, digest `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`.

## Immutable Direct-G evidence — do not rerun for reassurance

Behavior: run `33516084949`, HEAD `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`, TREE `857dc01e04f58ca59437e08710bcb194bf030ea4`, artifact `9803814288`, digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`; Record/Replay `28/28 PASS`, semantic replay PASS, stack PASS, hidden/cross-principal leak 0.

Principal Observation v4: run `33552816460`, source HEAD `3be666cc268456274204d39b2bd3c208f0d8c41e`, artifact `9818304005`; 28 paths, hidden-required 24, record/replay observations 1496/1496, unauthorized/private leak delta 0, cross-principal leak delta 0.

G requirement migration: run `33564749471`, artifact `9822685407`, digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`; G requirements Hidden 74, RNG 21, Replay 57, Decision 50; ABI V2.1 PASS; 17 negative fixtures rejected; verifier PASS.

## G3 work already closed — do not repeat

- principal-scoped DecisionEvent repair/hardening: run `33690697036`, artifact `9870061705`, digest `sha256:21bfde999292f5d3a3d1cc5f27e5236ab352972cedde7b32691ea5ad31fbe0cd` PASS.
- 53-SVar topology: run `33681121017`, artifact `9866293827`, digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b` PASS; `G81 = Direct28 + SVar53`; unresolved parents 0.
- topology hash-space mismatch fixed; AF parent actual-card binding fixed; 19-field AF case ABI aligned; target-SVar observer is observation-only.
- compile-scope defect from run `33742586083` closed by commit `3ca8c330287ef1f140b5be9e0c46187c762a7c7b`.
- Kindred Summons generic ChooseType reachability closed in run `33743144684`.
- raw Charm Choices ordinal selection removed by commit `1cff246a32df32788736576b4bd5e21ad73cdfec`; desired mode is chosen only by exact membership of opaque `ability_sub:<id>` in Forge's authoritative `MODE_SELECTION` set.
- Charm clone observation normalized narrowly by commit `28f4e7cdd6a35c488d4633cf8d77163a8aa2d5d9`; only Forge's documented runtime-added `StackDescription=SpellDescription` is ignored, broad subset matching is statically forbidden.

## Current confirmed qualification checkpoint — AF Behavior + ABI/Decision/RNG/Replay green

`LAST_CONFIRMED_CHECKPOINT = G3_AF_ABI_REPLAY_PASS_33748782606`

State-reconciliation checkpoint:
- `checkpoints/G3_STATE_RECONCILIATION_AF_ABI_PASS_5a2da789.md`

AF Behavior immutable evidence — do not rerun unless materially invalidated:
- HEAD `28f4e7cdd6a35c488d4633cf8d77163a8aa2d5d9`
- TREE `fa5cb7385b2724433cf877b11e890985adef2376`
- run `33745809012`
- job `100617880661`
- artifact `9889684290`
- digest `sha256:7a9b8a4e8dd993d419d55fa31763ef8d49ffc3927408bfdb4488724dd16d68e9`
- downloaded ZIP SHA256 exactly equals artifact digest.
- paths/behavior `21/21 PASS`.
- stack admission/resolution `21/21`.
- exact target-SVar reachability `21/21`; zero-count paths `0`; total target executions `25`.
- outer failure null; game completed true.

AF ABI / Decision / RNG / Replay immutable evidence — do not rerun unless materially invalidated:
- checkpoint `checkpoints/G3_AF_ABI_REPLAY_PASS_33748782606.md`
- workflow source HEAD `b599cb1550c3e04f099eb59dd4aae1e117078167`
- workflow source TREE `9944a7f8295222839f4efef92be562c84ebc09ef`
- run `33748782606` SUCCESS
- job `100627296583` SUCCESS
- artifact `9890829899`
- artifact digest `sha256:77fe10f72233e824169829a2e7526103cb0bacf8b06823379ce57f44472359eb`
- downloaded ZIP SHA256 retained by checkpoint and equal to GitHub digest.
- schema `commander-simulator-next.ws33-g-abi-request-evidence.v2`
- paths `21`
- Decision required/observed `9/9`
- RNG required/observed `4/4`
- Replay required `12`; deterministic Record/Replay request equality proven.
- request events `47`; identity scope `principal_id+token`.
- hidden identity retained false; silent fallback false; coverage mutated false.
- byte-identical Record/Replay retained for case summary, decision tape/events, RNG tape/events, and decision requests.

AF requirement cardinalities from the frozen cases:
- paths `21`
- Hidden required `19`
- RNG required `4` — `CLOSED`
- Replay required `12` — `CLOSED`
- Decision required `9` — `CLOSED`

No AF coverage promotion has occurred.

## AF Principal Observation / Hidden Information — implementation state

Still `OPEN` for `19/21`; no principal-observation qualification PASS exists yet.

Implemented and persisted:
- base adjudicator parameterized by `--expected-paths`; default remains `28` for Direct-G compatibility;
- exact Direct-G v15 vs AF v19 Case-ABI discrimination; unknown/mixed ABI fails closed;
- AF hidden-profile classification bound to executed target consumer `targetDispatch=f[17]`, `targetScript=base64(f[18])`, not source-parent dispatch/script;
- observation instrumenter accepts exactly one Direct-G or AF attribution anchor; missing/ambiguous anchors fail closed;
- AF attribution anchor `currentPath.set(spec.pathId);prepareSourceParentChoices(spec,sa);bindTargets(sa);`;
- campaign path coverage separated from optional/negative observation-event cardinality;
- strict positive lifecycle remains `(principal,card): SERVER_GRANT -> CLIENT_VISIBLE -> SERVER_REVOKE -> CLIENT_HIDDEN` with final hidden;
- focused workflow `.github/workflows/ws33-g3-svar-af-principal-observation-v4.yml` exists.

The old coarse process counter `pilot_visible_hidden_info_leaks=1` is not waived. It may only be superseded by source-required principal-scoped observation evidence proving correct entitlement, complete revocation, unauthorized/private leak delta `0`, and cross-principal leak delta `0`.

### Last adjudicated attempt

Immutable diagnostic checkpoint:
- `checkpoints/G3_AF_PRINCIPAL_OBSERVATION_OVERLAY_ORDER_FAIL_33755201667.md`

Run:
- source HEAD `52794dcf29c7d673630ad7d96e91f596af57aec9`
- source TREE `28597fcdcebfd4dde6ecbfe7e7c8bbc108a9e26d`
- run `33755201667` — `completed/failure`
- job `100647860029`
- artifact `9893240608`
- artifact digest `sha256:15203c5cab425e46c06b2142231a8f29de7f2a02b73af1442f39501fd0cd81b4`

First material failure: overlay composition before any Maven/runtime execution.

`WS33_OBSERVATION_FANOUT=FAIL public reveal host exception: expected anchor once, found 0`

Root cause is source-split misuse in the new workflow: it applied `apply-ws33-input-confirm.py` from immutable Direct-G Behavior source `d8af15cb...`, which predates the later Principal Observation base infrastructure expected by the current observation-fanout overlay. The immutable Direct-G Principal Observation v4 PASS run `33552816460` used successor source `3be666cc...`, where that base infrastructure is present. The fanout correctly failed closed.

Also found before retry: planned `EVIDENCE_SHA256SUMS.txt` creation would include/hash the output file itself due shell redirection. No evidence was accepted because the failed run never reached that step; fix this before retry.

No runtime behavior failure has been proved by run `33755201667`; AF Principal Observation remains `UNKNOWN/OPEN`, not PASS and not production behavior FAIL.

## Exact next atomic packages

1. Correct `.github/workflows/ws33-g3-svar-af-principal-observation-v4.yml` to use the current successor's Principal Observation base `apply-ws33-input-confirm.py` before observation-fanout, while keeping exact immutable AF stack/target/SVar behavior sources.
2. Fix evidence-hash self-inclusion in the same atomic workflow correction; do not loosen any fail-closed anchor.
3. Let the corrective commit trigger a fresh AF Principal Observation run; immediately persist run/job/source HEAD/TREE.
4. Adjudicate first material result. If the runtime reaches hidden-profile adjudication, unknown consumer semantics (including the hidden Manifest target consumer unless explicitly resolved) remain fail closed; do not waive them.
5. Only after a strict AF Principal Observation PASS with 21/21 Record/Replay campaign coverage, Hidden 19/19, transport `REMOTE_CLIENT_DELTA`, retained identity false, leak deltas `0`, complete required lifecycle, deterministic observations and coverage mutation false may AF be marked qualification-complete and `G3_AF_COMPLETE` be created.
6. Then qualify the remaining 32 non-AF G SVar paths through 33 real source-proven production event parent entrypoints; preserve the true two-parent Kang Prime path and prohibit direct target-SVar/trigger qualification.
7. Complete G3 `81/81`, materialize/promote only through authoritative WS33 campaign tooling, verify evidence/index/hashes, and freeze exact post-G3 successor before serial `ABC -> D -> E -> F`.

## Non-AF G queue already materialized, not yet qualified

`ws33_prepare_g_svar_event_cases.py`: exactly 32 effective paths / 33 source-proven event parents; modes ChangesZone12, Phase6, Attacks5, DamageDone4, SpellCast2, AttackersDeclared2, DamageDoneOnce1, Sacrificed1; direct target-SVar entry false.

## Serial queue after G3

Only after G3 reaches `81/81 PASS` with all evidence obligations and an exact frozen successor: `ABC -> D -> E -> F`.

Control expectations only until freshly computed from each successor: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
