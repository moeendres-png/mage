# WS33-C auto-run 34303790187 terminal FAIL-BY-DESIGN (adjudicated)

RUN = 34303790187 (push-triggered by the PASS+repartition commit itself)
SOURCE_HEAD = 7c6a3deea7
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
COVERAGE_PROMOTION = FALSE

## What happened

The repartition commit (partition now 8 EVIDENCED) retriggered the batch
workflow via the c-campaign/** path filter. Materialization correctly
refused: `WS33_C_BATCH_CHECK=FAIL path already evidenced (not declared
re-witness): forge-behavior-v2:ed6d9d36…`.

## Adjudication

This is the anti-double-credit gate working EXACTLY as designed: batch-1
definitions claim paths the owned partition now records as EVIDENCED, so
no second credit can issue from a stale batch. No harness/overlay/model
defect. No repair needed and none made; batch-1 inputs stay frozen.
Cancellation was attempted but the run had already completed (fast fail
at materialization, ~1 min, no Forge build spent).

Classification: FAIL-BY-DESIGN (correct rejection), not a witness failure.
EVIDENCED_PATH_COUNT = 8 / REMAINING_UNKNOWN_COUNT = 692 (unchanged).

## Exact next action

Batch-2 selection from remaining template-113 STATE_ONLY (rank: targeted-ETB
authoritative-target protocol vs Effect-static vocabulary vs phase-family
investigation); fresh definitions + digest; PENDING; run; adjudicate.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
