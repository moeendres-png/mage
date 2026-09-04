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

`LAST_CONFIRMED_CHECKPOINT = G3_NON_AF_EVENT_RUNTIME_RUN_33820842986_FAILURE`

Checkpoint:
`research/greenfield-qualification/actual-card-behavior/ws33/checkpoints/G3_NON_AF_EVENT_RUNTIME_RUN_33820842986_FAILURE.md`

Run `33820842986` / job `100862957388` is terminal `failure`. Its source is `71a64f9cd483daf5fbbd1ada5bbde157a73e142e`, tree `300edfc71b11041069885c03978ee14590999b52`, artifact `9918266289`, digest `sha256:693c5b2767e3758668dc38183aa21f543ca0fe08faf3d1e2d8d3c3c98154dfa6`; the downloaded ZIP independently re-hashes exactly to that digest.

Steps 1–14 PASS. Step 15 is the first failure. Replay/source-chain are skipped. Coverage promotion remains FALSE.

The first source-proven parent (`Ingenious Smith`, `ChangesZone`, `TrigDig -> Dig`) is still admission/binding/execution `1/1/0`, has zero resolution callbacks, and now also zero correlated `MagicStack` lifecycle events. Observation-only `PlaySpellAbility` telemetry identifies the first production rejection as `OPTIONAL_COST_SELECTION_NULL` immediately after `PLAY_SPELL_ENTRY`. Therefore `chooseOptionalAdditionalCosts(p, sa) -> controller.getAbilityToPlay(original.getHostCard(), abilities)` returns null before `playAbility(...)`, target setup, payment, `addAndUnfreeze`, or `MagicStack.add`.

A passing control parent proceeds through `OPTIONAL_COST_SELECTION_OK`, all pre-cost checks, payment, `ADD_AND_UNFREEZE`, `ADD_ENTER`, `STACK_PUSH`, `FIZZLE_RESULT=false`, and resolution. The diagnostic boundary is therefore functioning.

No repair is authorized until actual option cardinality and adapter behavior are inspected.

## G3 immutable evidence — do not rerun without invalidation

### Topology

- run `33681121017` SUCCESS; job `100417671589`; artifact `9866293827`; digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`.
- partition: `G81 = Direct28 + SVar53`; SVar = `AF21 + non-AF32`; real non-AF parent entrypoints `33`; unresolved parents `0`.

### Direct-G 28

- behavior run `33516084949`; artifact `9803814288`; digest `sha256:493f3549b6483d4fea9644f3a0216deb108a9ac581b651ff3e083499bcb14b5a`; 28/28 Record/Replay PASS.
- Principal Observation v4 run `33552816460`; artifact `9818304005`; hidden/observation gates PASS.
- requirement artifact `9822685407`; digest `sha256:81e1e24551403453e4dd32e9ed65951cbaca2776cc993eddf475b4214a67a424`; ABI v2.1 + 17/17 negatives PASS.

### AF21

- Runtime v2 run `33773548765` PASS.
- ABI/Decision/RNG/Replay v2 run `33773805031` PASS.
- Principal Observation v5 run `33774853355`; artifact `9901438964`; digest `sha256:2e60f7c79ad642f3f3942db4b3e84a9392cde5662126c0eb84153a3f0469cb5d`; PASS.

## Current G3 frontier

- total G3: `81`
- immutable Direct-G qualified: `28`
- immutable AF qualified: `21`
- remaining effective paths: `32`
- remaining production parents: `33`
- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`

Remaining production-parent modes: ChangesZone `12`, Phase `6`, Attacks `5`, DamageDone `4`, SpellCast `2`, AttackersDeclared `2`, DamageDoneOnce `1`, Sacrificed `1`. Kang Prime retains both source-proven parents.

## Non-AF runtime attempt chain

1. `33797779388`: manifest-file hash vs consumer-model hash confusion; repaired.
2. `33798342466`: pinned MagicStack declaration anchor mismatch; repaired.
3. `33798608932`: first Ingenious parent `0/0/0`; ChangesZone fixture used `ZoneType` enums instead of production zone-name Strings; repaired by `.name()`.
4. `33816948410`: first parent becomes `1/1/0`; 24 parents `1/1/0`, one PASS, eight later event-specific failures.
5. `33817799382`: request-trace transformer lacked lineage Event ABI; repaired.
6. `33818067742`: diagnostic Java `TreeMap` compile failure; repaired.
7. `33818428322`: lineage gives `1/1/0`, `resolutionCallbacks=0`; matcher false-negative excluded.
8. `33819960784`: lifecycle overlay applies and record campaign reproduces failure; harness did not yet consume lifecycle callback.
9. `33820366293`: parent-correlated lifecycle proves first Ingenious parent never enters `MagicStack.add`; fizzle and stack-target rejection excluded.
10. `33820842986`: observation-only PlaySpellAbility stages prove earliest common rejection is `OPTIONAL_COST_SELECTION_NULL` inside `chooseOptionalAdditionalCosts`, before `playAbility(...)`.

## Exact next atomic package

1. Inspect pinned `GameActionUtil.getAdditionalCostSpell(original)` and the branch/runtime overlays implementing `PlayerControllerHuman.getAbilityToPlay` / external decision transport.
2. Establish directly for failing and passing parents the actual returned option cardinality and semantic differences; do not infer singleton behavior merely from API shape.
3. Determine whether null is caused by a missing external-pilot binding for a discretionary multi-option choice or by routing a non-discretionary singleton through a decision surface.
4. Preserve the Rules/Pilot boundary: authoritative rules options come from the core; the pilot chooses only among genuinely discretionary legal alternatives. No first/default/random/pass/cancel fallback is permitted.
5. Repair only the confirmed systemic adapter/runtime defect. No Ingenious/card/path special case.
6. Commit one repair; allow exactly one successor `ws33-g3-svar-event-runtime.yml` run; immediately persist run/job/source HEAD/TREE.
7. Terminally adjudicate. If the first failure advances to a later prerequisite such as `SETUP_TARGETS=false`, freeze that new failure before further repair.
8. Continue until non-AF Runtime strict PASS for 32 effective paths / 33 real parents, then freeze Runtime before separate ABI/Decision/RNG/Replay certification and Principal Observation/Hidden31 qualification.
9. Only after Direct28 + AF21 + non-AF32 satisfy all required contracts may G3 be promoted/frozen and serial closure proceed `ABC -> D -> E -> F`.

Control expectations remain non-authoritative until fresh successor computation: post-G3 PASS366/UNKNOWN3822; post-ABC 1920/2268; post-D 2840/1348; post-E 3869/319; post-F 4188/0.
