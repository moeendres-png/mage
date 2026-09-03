# WS33 G3 AF runtime v2 — queued-run checkpoint

Status: `RUN_QUEUED_NO_ADJUDICATION`

Evidence classification: `DIRECTLY_VERIFIED` GitHub Actions control-plane state only. This checkpoint is **not** runtime evidence and must never be interpreted as PASS or FAIL.

## Exact queued identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `WS33 G3 SVar AF runtime v2 hidden witness`
- workflow path: `.github/workflows/ws33-g3-svar-af-runtime-v2.yml`
- run: `33769086465`
- job: `100694379650`
- workflow source HEAD: `7fc18ccd062278d8690e77c0b04fad44bc9b213b`
- workflow source TREE: `992da510930c5e0c9b919feb3e4319655e1f6aec`
- status at checkpoint: `queued`
- conclusion: `null`
- job runner_id: `0`
- job steps: none allocated yet
- repository-wide in-progress runs at observation time: `0`
- repository-wide queued runs at observation time: exactly this run

## Interpretation

No qualification code has executed yet. The state is an external GitHub-hosted runner allocation wait, not a WS33 test result.

Do not:

- cancel and replace this run merely to obtain a different queue position;
- create a second material runtime run while this exact run is queued;
- promote any AF coverage from this state;
- infer PASS/FAIL from queue duration.

## Resume rule

On resume, query run `33769086465` first.

- If still queued: retain this checkpoint and make no qualification claim.
- If in progress: inspect the same run/job; do not start a duplicate.
- If completed: fetch exact job steps and immutable artifact identity/digest, inspect the first failing step or all PASS assertions, and persist a new final run-adjudication checkpoint before starting AF ABI v2.

AF behavior v2 qualification: `UNKNOWN`

Coverage promotion: `FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
