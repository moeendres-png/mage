# WS33 G3 AF Principal Observation v4 — run 33762514428 first-failure checkpoint

Status: `RUN_ADJUDICATED_FAIL_CLOSED`

Evidence classification: `DIRECTLY_VERIFIED` from GitHub Actions run/job/artifact plus immutable artifact contents.

## Exact run identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow source HEAD: `9fbf7729eaecbd724d38f598cb5b0bdcf8352212`
- workflow source TREE: `c5ec075fb35048940ce6da4a8a189f9b107e4c14`
- run: `33762514428`
- job: `100672075188`
- artifact: `9896399874`
- artifact name: `ws33-g3-svar-af-principal-observation-v4-33762514428`
- artifact digest: `sha256:77ea9ebd237406c47ba1d8316743ab9b2af8efe1a87a6ede1da89f52c2f40527`

## Step adjudication

The repaired workflow passed all prerequisites through fresh runtime execution:

- exact serial ancestry: PASS
- immutable AF ABI consumption: PASS
- exact source pins: PASS
- runtime overlays: PASS
- instrumented harness + Direct-G anchor compatibility: PASS
- parser/fail-closed regressions: PASS
- fresh record execution: PASS
- tape-driven replay execution: PASS
- observation-only nonperturbation against immutable AF ABI record: PASS

The first failing step is exactly:

`Strict AF target-consumer principal-observation adjudication`

Final JSON status: `FAIL_CLOSED`, `failure_count=4`.

## Exact remaining failures

Record and replay fail symmetrically on only two path identities:

1. `forge-behavior-v2:47f0f37a5823140c6fe301fc21730cff8d227057`
   - source parent dispatch: `ChangeZone`
   - executed target consumer: `Manifest`
   - implementation: `forge.game.ability.effects.ManifestEffect`
   - verifier profile: `UNKNOWN_HIDDEN_CONSUMER`
   - record grants: `0`
   - replay grants: `0`
   - failures: `record_unknown_hidden_consumer_profile`, `replay_unknown_hidden_consumer_profile`

2. `forge-behavior-v2:a817142bdd146d535481895c85387094a2c7ad62`
   - source parent dispatch: `DealDamage`
   - executed target consumer: `Scry`
   - implementation: `forge.game.ability.effects.ScryEffect`
   - verifier profile: `POSITIVE_TEMPORARY_REQUIRED`
   - reason: `authoritative hidden-card decision`
   - record grants: `0`
   - replay grants: `0`
   - failures: `record_missing_positive_observation`, `replay_missing_positive_observation`

No other AF path fails principal-observation adjudication.

## Coarse signal after validator repair

The only non-zero raw summary column-9 signal is the expected `RevealHandEffect` path:

`forge-behavior-v2:17f8532940a8967b06c70c70431c410d86c56c19`

It is `1` in both record and replay, with cross-principal delta `0`; the repaired lifecycle-bound coarse-signal contract no longer fails on it. This proves the prior validator root cause is closed.

## Invariants retained

- `record_path_coverage=21`
- `replay_path_coverage=21`
- `hidden_required_paths=19`
- `cross_principal_delta_required=0`
- `retained_hidden_identity_payload=false`
- `principal_transport=REMOTE_CLIENT_DELTA`
- `coverage_mutated=false`
- record/replay observation event count: `504 / 504`
- raw runtime row status: all 21 PASS
- stack admission/resolution: all 21 `1/1`

## Serial next step

Do not weaken the verifier by API-name exception. Inspect the exact pinned-Forge `ManifestEffect` and `ScryEffect` execution shapes, their parent scripts, and current official rules semantics. Classify whether each path is:

- a genuine positive principal-observation obligation requiring a systemic transport repair;
- a negative/transition-only hidden path that must not manufacture observation;
- or an already-public/revealed consumer whose current profile is wrong.

Any classifier change must be source- and rules-derived and accompanied by fail-closed regressions. Any runtime repair must preserve Rules/Pilot separation and record/replay determinism.

AF Hidden / Principal Observation: `UNKNOWN`

Coverage promotion: `FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
