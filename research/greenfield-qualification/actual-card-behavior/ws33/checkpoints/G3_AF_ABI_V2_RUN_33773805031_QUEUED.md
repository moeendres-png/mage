# WS33 G3 AF ABI/replay v2 — queued-run checkpoint

Status: `RUN_QUEUED_NO_ADJUDICATION`

Evidence classification: `DIRECTLY_VERIFIED` GitHub Actions control-plane state only. This checkpoint is not a qualification result.

## Exact resume identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `WS33 G3 SVar AF ABI replay v2`
- workflow path: `.github/workflows/ws33-g3-svar-af-abi-replay-v2.yml`
- run: `33773805031`
- job: `100710378109`
- workflow source HEAD: `fe63c66a7be6215dffd4da85fc4cf7bf1de63b72`
- workflow source TREE: `6faa1a272201c5101fdf1533f8540ce99a4a3f8c`
- status at checkpoint: `queued`
- conclusion: `null`

## Bound runtime-v2 baseline

- certified runtime source HEAD: `bd9998a30bd4f34603592aa06e7b16d2d3320047`
- certified runtime artifact id: `9900656730`
- certified runtime artifact digest: `sha256:b339b3eba6daaee5b7f59e9e3c05a7af611c1479ebd3d7b6e2c94d04f72e0708`
- strengthened witness source HEAD: `b3d02af402e55a65b11dcfec94def62be469a7a0`

## Resume rule

Query run `33773805031` first. Do not start a duplicate ABI v2 run while it is queued or in progress. On completion, inspect job steps and immutable artifact identity/digest; persist first material failure or full PASS before starting principal-observation v5.

AF runtime v2: `PASS`

AF ABI/replay v2: `UNKNOWN`

AF Hidden / Principal Observation: `UNKNOWN`

Coverage promotion: `FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
