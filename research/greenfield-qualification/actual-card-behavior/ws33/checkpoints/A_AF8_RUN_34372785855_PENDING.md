# WS33-A AF8 run 34372785855 — PENDING (registered 2026-09-09)

Status: **PENDING**. `COVERAGE_PROMOTION=FALSE`. `COVERAGE_MUTATED=FALSE`.

## Frozen registration

- SOURCE_HEAD: `ef836661b3c0bf13535f0f417e36367eb6fd540e` (run `headSha` verified equal at registration)
- SOURCE_TREE: `8634200aae45b9cd0cfba0285e208d41a32add99`
- RUN: `34372785855`; JOB: `102537936108` (`af8`); dispatch: `workflow_dispatch` on
  `work/ws33-a-trigger-closure-20260907`
- Expected artifact: `ws33-abc-a-rest-svar-af8-34372785855` (retention 90d)
- Workflow file: `.github/workflows/ws33-abc-a-rest-svar-af8-runtime.yml` at SOURCE_HEAD
- Immutable deps (workflow-pinned): FORGE_PIN `8c7e9afb…f8928`;
  ROUTE_RUN `34063748962` / ROUTE_ARTIFACT `9998291348` /
  ROUTE_DIGEST `sha256:6465…f9d0e9` / ROUTE_SOURCE `48cb9a01…263a1`;
  DIRECT_RUNTIME `d8af15cb…3f272`; WS01 `bf089ea8…9684`; WS12 `80743bd…04d4`;
  WS32 `6ca2a7b…3717a9`; WS31_HIST `b09fe7c…bbf007`.

## Source content at freeze (what this run executes)

- Observer wiring: stack-resolution-reachability + a-rest-play-stage-observer + mana-cancel-boundary
  in Direct31 v2/v5 order after svar-reachability, with PASS/rail gates.
- Hardened AF8 evidence: identity-bound target rows (source/root/child/actor + before/after),
  per-policy selection witness with forced classification, GUI_GET_INTEGER-scoped positive-X policy.
- Fail-closed adjudicator with target-detail, selection, and success-gated play-stage gates.
- 38/38 local unit tests green; local full-stack compile green; local Record+Replay executed
  (7/8 PASS, Profane FAIL_CLOSED on the shared WS01 unbounded-X boundary — see repairs checkpoint).

## Expected terminal shape (local replica prediction, NOT a verdict)

- 7/8 paths PASS with Decision+Hidden+Replay+target+selection+stage evidence.
- Profane `fa2b8db7` FAIL_CLOSED at `Consume`? No — at Record:held `UNSUPPORTED_DECISION_PATH:
  GUI_GET_INTEGER` (unbounded X range `[0, Integer.MAX_VALUE]`), failing the run's adjudication
  unless the shared boundary changed. A green workflow alone is not PASS; adjudicate the artifact.

## Exact next action

Poll run `34372785855` to terminal status; on completion download artifact
`ws33-abc-a-rest-svar-af8-34372785855`, verify digest/metadata/SOURCE_CHAIN binding to SOURCE_HEAD,
run the new adjudicator over Record/Replay, persist terminal PASS/FAIL with root-cause
classification before any further source change.

`TURN_STATUS=INTERRUPTED`. `TASK_COMPLETE=NO`.
