# WS33-A AF8 run 34405600698 — PENDING (reconciled + contract repair, registered 2026-09-09)

Status: **PENDING**. `COVERAGE_PROMOTION=FALSE`. `COVERAGE_MUTATED=FALSE`.
Predecessor run `34403594655`: semantic gate PASS 8/8 (`failure_count=0`) but workflow
step red on the stale observation-samples byte-`cmp` (transport multiplicity, Case A
contract defect). Root cause classified in `A_AF8_RUN_34403594655_FAIL.md`. This
replacement is justified (not blind): it carries only the qualified line's accepted
contract repair, no semantic change.

## Frozen registration

- SOURCE_HEAD: `1d19be5ee892a3ff142be780985366da2846ef21` (run `headSha` verified equal)
- SOURCE_TREE: `7912ca7674406c2de8e0e9cb2f84f41deaca9074`
- RUN: `34405600698`; JOB: `102647707299` (`af8`); dispatch: `workflow_dispatch` on
  `work/ws33-a-trigger-closure-20260907`
- Expected artifact: `ws33-abc-a-rest-svar-af8-34405600698` (retention 90d)
- Delta vs predecessor source `b2289eb6e8`: workflow drops the non-semantic
  `AF8_CLIENT_OBSERVATION_SAMPLES.tsv` byte-`cmp` (adjudicator >=1/mismatch-0 contract
  governs both sides) + new `test_ws33_af8_observation_replay_contract.py`
  byte-identical to the qualified AF8 line. Runtime/hardener/adjudicator/overlay
  identical to the reconciled source.
- Immutable deps unchanged (FORGE_PIN, route run/artifact/digest/source, WS01/WS12/
  WS32/WS31-hist pins).

## Expected terminal shape (predicted, NOT a verdict)

- All 18 steps SUCCESS; adjudication PASS 8/8 with Profane carrying a `NUMBER_ENUM`
  `POSITIVE_X_ANNOUNCEMENT` selection row; Record/Replay byte-identical semantic
  tapes/events/stages; sealed artifact for eight-candidate extraction. The only
  accepted non-identical file is the transport-multiplicity samples file.

## Exact next action

Poll run `34405600698` to terminal status; download + verify digest + SOURCE_CHAIN
binding to SOURCE_HEAD; run the frozen adjudicator over remote Record/Replay;
on PASS, extract eight sealed per-path evidence candidates and hand off with
`COVERAGE_PROMOTION=FALSE`. On FAIL, persist root-cause classification before repair.

`TURN_STATUS=INTERRUPTED`. `TASK_COMPLETE=NO`.
