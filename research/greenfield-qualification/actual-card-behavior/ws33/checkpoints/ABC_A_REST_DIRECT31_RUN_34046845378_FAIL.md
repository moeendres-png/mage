# WS33 ABC — A-rest Direct31 Runtime v2 — TERMINAL FAIL

Evidence class: DIRECTLY_VERIFIED.

## Frozen run

- RUN: `34046845378`
- JOB: `101523300459`
- SOURCE_HEAD: `e5df74c1b13d140b78bb1ff58dd0f59fe6123862`
- SOURCE_TREE: `8c0453a24c77c4c96bd244f2cbbe95d7ef10e7ae`
- CONCLUSION: `failure`
- ARTIFACT_ID: `9993373902`
- ARTIFACT_DIGEST: `sha256:f7f3e93849eed077cc6f15bf4049dcbef0a55df496a43545141ae9f7597dc37a`
- downloaded ZIP SHA256 independently verified: `f7f3e93849eed077cc6f15bf4049dcbef0a55df496a43545141ae9f7597dc37a`

## Terminal stage

The run failed before Maven/actual-card witness execution. Artifact contains no `record/case-summary.tsv`, no decision/RNG tapes, and no runtime log.

All new preparation components completed successfully:

- `WS33_A_REST_PLAY_STAGE_OBSERVER=PASS semantics_mutated=FALSE booleans_mutated=FALSE`
- `WS33_A_REST_DIRECT_HARNESS=PASS`
- `WS33_A_REST_DIRECT_CASE_ABI=PASS`
- `WS33_A_REST_DIRECT_IMPLEMENTATION=forge.game.spellability.TargetRestrictions`
- `WS33_A_REST_DIRECT_CASE_ABI_RULES_MUTATION=0`
- `WS33_A_REST_DIRECT_REMOTE_ACTOR=PASS actor_slot=1 opponent_slot=2 phase=FORGE_MAIN1 legality_bypass=0`
- `WS33_A_REST_DIRECT_OBSERVATION=PASS path_scoped=true play_stage_observer=true rules_mutation=0`

## Root cause

`ws33_run_a_rest_direct31_runtime_v2.sh` used an incorrect exact grep contract. It expected one combined line:

`WS33_A_REST_DIRECT_CASE_ABI=PASS implementation=forge.game.spellability.TargetRestrictions rules_mutation=0`

The authoritative ABI repair script emits those attestations as three separate lines. Therefore the shell gate exited despite all preparation components passing.

Classification: `HARNESS_DRIVER_GATE_FIX`.

No Forge Rules Core defect is implicated. No witness path executed. No coverage mutation/promotion occurred.

- COVERAGE_MUTATED: `FALSE`
- COVERAGE_PROMOTION: `FALSE`
- PASS remains `488`
- UNKNOWN remains `3700`
- A_UNKNOWN remains `57`
