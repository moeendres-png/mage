# WS33 G3 AF principal observation v5 — started-run checkpoint

Status: `RUN_IN_PROGRESS_NO_ADJUDICATION`

Evidence classification: `DIRECTLY_VERIFIED` GitHub Actions control-plane state only. This checkpoint is not a qualification result.

## Exact resume identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `WS33 G3 SVar AF principal observation v5`
- workflow path: `.github/workflows/ws33-g3-svar-af-principal-observation-v5.yml`
- run: `33774853355`
- job: `100713875152`
- workflow source HEAD: `33b61704dbe69ace66b5a6d1e68ca09800ea8668`
- workflow source TREE: `8a191eebe0f8c6da9c4f01c22cbee3e05d550560`
- status at checkpoint: `in_progress`
- conclusion: `null`

## Exact strengthened inputs

- AF ABI/replay v2 source HEAD: `fe63c66a7be6215dffd4da85fc4cf7bf1de63b72`
- AF ABI/replay v2 artifact id: `9901008043`
- AF ABI/replay v2 artifact digest: `sha256:bf58a7154e8e2623bc9e6f4acf10c933b7d4fd692a357a643b881c586f4c15ef`
- certified AF runtime-v2 source HEAD: `bd9998a30bd4f34603592aa06e7b16d2d3320047`
- certified AF runtime-v2 artifact id: `9900656730`
- certified AF runtime-v2 artifact digest: `sha256:b339b3eba6daaee5b7f59e9e3c05a7af611c1479ebd3d7b6e2c94d04f72e0708`
- strengthened witness source HEAD: `b3d02af402e55a65b11dcfec94def62be469a7a0`
- shape-aware Manifest classifier: `ws33_adjudicate_g_principal_observation_v5.py`

## Resume rule

Query run `33774853355` / job `100713875152` first. Do not launch a duplicate v5 run while it is queued or in progress. On completion, inspect the first failed material step or, on full success, freeze run/job/artifact/digest before any non-AF/G32 work.

AF runtime v2: `PASS`

AF ABI/replay v2: `PASS`

AF Hidden / Principal Observation: `UNKNOWN`

Coverage promotion: `FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
