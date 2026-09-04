# WS33 G3 non-AF event runtime — run 33856299908 failure

Status: `FAIL / PRE-RUNTIME / NOT BEHAVIOR EVIDENCE`

## Immutable identity

- run: `33856299908`
- job: `100970288737`
- source HEAD: `581ae03dc269c38c51f8ba4f79d69b780ce7f1bd`
- source TREE: `bd3742b90c49726e5ead38ec76342c9f61737a29`
- artifact: `9930349524`
- artifact digest: `sha256:248db8fb09bc3feefdef80b17edd1a3cd2e833a3d05fe18a5331b160baf14bab`
- independently downloaded ZIP SHA256: `248db8fb09bc3feefdef80b17edd1a3cd2e833a3d05fe18a5331b160baf14bab` — exact match

## Step adjudication

- source pins: PASS
- WS01/WS05/WS06/input-confirm/observation-fanout/external-card-lifetime/stack-target/target-selection overlays: PASS
- Step 11 `Apply qualified runtime overlays plus observation-only event reachability`: FAIL
- Step 12+ harness/runtime/adjudication/replay: SKIPPED
- artifact upload: PASS

No record campaign executed. This run provides zero new card-behavior qualification evidence and cannot affect coverage.

## First material failure

The observation-only diagnostic patcher stopped fail-closed with:

`WS33_TRIGGER_REACHABILITY=FAIL spawned trigger canRun-gate diagnostics: expected one match, got 0`

The `isTriggerActive(...)` diagnostic replacement had already matched; the overly strict whole-method textual anchor for pinned `canRunTrigger(...)` did not match the exact pinned Forge source. This is a diagnostic patch-anchoring defect, not a trigger-legality or engine result.

## Required next action

Read the exact pinned `TriggerHandler.canRunTrigger(...)` implementation at Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`, replace only the brittle diagnostic anchor with exact/smaller fail-closed anchors, and run exactly one successor. Preserve all production boolean expressions and ordering. Continue to log only dynamically spawned triggers; do not repair or special-case Study Hall before the exact rejection gate is observed.

`G3_NON_AF_STATUS = UNKNOWN`
`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
