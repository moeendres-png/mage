# WS33-A AF8 run 34377848619 — PENDING (replacement, registered 2026-09-09)

Status: **PENDING**. `COVERAGE_PROMOTION=FALSE`. `COVERAGE_MUTATED=FALSE`.
Predecessor run `34372785855`: terminal FAIL, adjudicated (24 failures, all Profane +
strict-parser coverage consequence; 7/8 paths clean). Root causes classified in
`A_AF8_RUN_34372785855_FAIL.md`. This replacement is justified (not blind): it carries the
repaired replay-step witness assertion (`1419a9e213`) whose absence failed the predecessor at
step 15 after green Record+Replay execution.

## Frozen registration

- SOURCE_HEAD: `9d72a192886e9bad0b831f590da5dabaea53261a` (run `headSha` verified equal)
- SOURCE_TREE: `3941baae4f821b7ae45275003f001a62c841b6fe`
- RUN: `34377848619`; JOB: `102555058095` (`af8`); dispatch: `workflow_dispatch` on
  `work/ws33-a-trigger-closure-20260907`
- Expected artifact: `ws33-abc-a-rest-svar-af8-34377848619` (retention 90d)
- Delta vs predecessor source `ef836661b3`: workflow replay-witness assertion fix only
  (`test -f` + dropped witness byte-cmp); runtime/hardener/adjudicator identical.
- Immutable deps unchanged (FORGE_PIN, route run/artifact/digest/source, WS01/WS12/WS32/WS31 pins).

## Expected terminal shape (predicted, NOT a verdict)

- Replay step green; adjudication FAIL_CLOSED with Profane-only failures (shared WS01
  unbounded-X boundary, open coordinator item); 7/8 paths with full Decision+Hidden+Replay+
  target+selection+stage evidence; sealed artifact for candidate extraction.

## Exact next action

Poll run `34377848619` to terminal status; download + verify + adjudicate its artifact;
on the predicted shape, extract the seven sealed per-path evidence candidates and hand off
with the Profane shared-boundary question. No further source change before adjudication.

`TURN_STATUS=INTERRUPTED`. `TASK_COMPLETE=NO`.
