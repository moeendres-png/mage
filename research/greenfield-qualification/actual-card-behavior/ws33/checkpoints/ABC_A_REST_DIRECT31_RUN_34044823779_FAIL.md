# WS33 ABC A-rest Direct31 — run 34044823779 FAIL

Status: `FAIL`
Evidence classification: `DIRECTLY_VERIFIED` for run/artifact/runtime rows; `CODE_DERIVED` for failure clustering.

## Frozen run identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `.github/workflows/ws33-abc-a-rest-direct31-runtime.yml`
- source HEAD: `ccfabf7517334f5ee166e5f80f76971e44603818`
- source TREE: `0d5c1ab6b130143b20d44218dcc1a5e13ed06584`
- run: `34044823779`
- job: `101517903398`
- run attempt: `1`
- conclusion: `failure`
- artifact: `9992826552`
- artifact name: `ws33-abc-a-rest-direct31-runtime-34044823779`
- artifact digest: `sha256:68ff732479197e8e85491b21ba764957ae7c300f0d11b49b2683bb4bfe1110f2`
- topology input artifact: `9980023181`
- topology input digest: `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Independent artifact checks

Downloaded ZIP sha256 exactly matches GitHub artifact metadata:

`68ff732479197e8e85491b21ba764957ae7c300f0d11b49b2683bb4bfe1110f2`

The embedded immutable A-rest topology remains intact and the generated harness reports:

- `WS33_A_REST_DIRECT_HARNESS=PASS`
- `WS33_A_REST_DIRECT_CASE_ABI=PASS`
- evidence implementation: `forge.game.spellability.TargetRestrictions`
- rules mutation from ABI repair: `0`

The previous compile defect is therefore closed for this run. Maven compiled and executed the 31-case actual-card campaign.

## Runtime evidence

`record/case-summary.tsv`:

- rows: `31`
- schema width: `21` for all rows
- PASS rows: `4`
- FAIL rows: `27`
- coarse hidden leaks: `0` on every row
- cross-principal leaks: `0` on every row
- process completed: `true`
- outer process failure: `null`

The four locally successful source-root paths are not promoted from this failed campaign.

### Failure cluster 1 — principal observation boundary

Exactly `21` paths fail with:

```text
UNSUPPORTED_DECISION_PATH: hidden authoritative Card choices require RemoteClient principal observation
```

These paths reached the actual source ability / Decision boundary; many already have stack admission and source-root resolution callbacks before a later hidden-card choice. The failure is the expected strict hidden-information boundary: hidden authoritative card options cannot be delegated until the selecting principal has an actor-scoped RemoteClient observation context.

Classification: `HARNESS_OBSERVATION_BINDING_GAP`, not a TargetRestrictions legality defect. Existing G3 qualification uses a separate path-scoped `ExternalObservationTrace` principal-observation campaign for exactly this contract. The A-rest Direct31 campaign must be instrumented with that qualified observation route rather than relaxing the strict decision boundary.

### Failure cluster 2 — PlaySpellAbility pre-admission rejection

Exactly `6` paths fail before source-root stack admission with:

```text
Forge PlaySpellAbility rejected exact source path
```

Affected effective path IDs:

- `forge-behavior-v2:728d346f8c02e5ba4c32cb442b31e65ee8d6ef30`
- `forge-behavior-v2:7dd42ac73fbe69450709d85f876962984e2d55a5`
- `forge-behavior-v2:9a879f3294d0236b6ed9dc829b10750a4aa8f262`
- `forge-behavior-v2:dd2997f095bef3d2bfa30b52f4bb24c3df5f8aec`
- `forge-behavior-v2:dd2f9dfad2fba886a0fa66300b8ab654ad501b86`
- `forge-behavior-v2:ed8a78e3c93cbd67fc879e71bd0133012e07e1e1`

No decision event was emitted for these six. They require precondition-level diagnosis (zone/timing/ability-kind/cost/target fixture) before another runtime attempt. No Rules Core defect is inferred from the generic false return.

## Replay state

Fresh replay did not run because the record adjudication gate correctly failed closed first. The produced record tape is therefore diagnostic only and cannot serve as qualification evidence.

## Invariants

- `RECORD_PATHS_EXECUTED=31`
- `RECORD_PASS_DIAGNOSTIC_ONLY=4`
- `RECORD_FAIL=27`
- `REPLAY_EXECUTED=FALSE`
- `COVERAGE_MUTATED=FALSE`
- `COVERAGE_PROMOTION=FALSE`
- `A_REST_UNKNOWN=57`
- `DIRECT31_RUNTIME_PASS=FALSE`

Next repair must preserve the strict hidden-information boundary and separately diagnose the six Forge pre-admission rejections. No failed-row or locally successful-row status may be promoted from this run.
