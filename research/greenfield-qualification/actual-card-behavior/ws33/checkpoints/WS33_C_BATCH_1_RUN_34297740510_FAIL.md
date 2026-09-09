# WS33-C Batch 1 R3 run 34297740510 terminal FAIL (adjudicated)

RUN = 34297740510
JOB_CONCLUSION = failure (step "Execute batch Record")
SOURCE_HEAD = 3e2f19cec9
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = ws33-c-abilitysub-batch-34297740510 (diagnostics + logs)
COVERAGE_PROMOTION = FALSE

## What the R3 rules achieved (DIRECTLY_VERIFIED from run log)

- Tripwire classification functional: zero UNEXPECTED_DECISION failures.
  Incidental mainLoopStep queries recorded, chopper singleton consultation
  (options=1) accepted as declared.
- Cap via-move registration fix CONFIRMED: fixture reached matching stage
  (no stack error).

## New findings requiring R4 diagnosis (all fail-closed, no false PASS)

1. DUPLICATE_PARENT_EVENTS: 6/7 ETB executions fail with "parent
   attribution ambiguous candidates=2" for the link parent api. Engine
   self-resolution by effects excluded by pin source inspection (no effect
   calls AbilityUtils.resolve/resolveSubAbilities). Same-id vs distinct-id
   and subParam details not yet evidenced. R4 enriches the ambiguity error
   with full candidate + event dumps. No behavior change.
2. GNARLBARK_SILENT_EOT: zero parent events across the whole EOT execution;
   devModeSet sets turn player (PhaseHandler pin lines), so turn mismatch
   is excluded as root cause. R4 enriches the no-parents error with
   phase/turn/game-over/stack snapshot to pinpoint (e.g. loop exit via
   game-over vs trigger never waiting).

Both direct-child negatives PASSED again.

## Classification

- R4 scope: diagnostics enrichment only (error-message content). No
  matching/contract/overlay/definition change; batch digest unchanged.
- No engine defect demonstrated. No Sol escalation.

EVIDENCED_PATH_COUNT = 1 / REMAINING_UNKNOWN_COUNT = 699 (unchanged)

## Exact next action

Commit FAIL + R4 enrichment, push, register diagnostic PENDING, read event
dumps from diagnostics, then targeted R5.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
