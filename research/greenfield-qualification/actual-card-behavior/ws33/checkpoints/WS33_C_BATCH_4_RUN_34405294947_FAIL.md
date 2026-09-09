# WS33-C Batch 4 R8-fix run 34405294947 terminal FAIL (independently adjudicated)

RUN = 34405294947
JOB = 102646709421 (completed/failure)
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
WORKFLOW_SOURCE_HEAD = 4f33837d7286a49ef4c4b5eabef603ccc5d7e68a
WORKFLOW_SOURCE_TREE = 899caadd06e9fab1a9770294e1268cb108d6d8ca
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10125163409 (ws33-c-abilitysub-batch-34405294947)
BATCH_ID = WS33_C_BATCH_4
BATCH_DIGEST = b9aa07cec3b284ea75bada8b75f1a33b98c286daa7fc9717f64d0e76f39cacd0
GATE = generated/evidence/WS33_C_BATCH_GATE.json NOT PRODUCED (2/3 markers)
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Independent verification (immutable artifact bytes, local 2026-09-09)

- Plan digest matches PENDING (b9aa07ce...); diagnostics exactly 1 row.
- kappa-etb-other: 7/7 record assertions PASS, TECHNICALLY_CONFORMANT.
- gateway-etb-other: 4/4 record assertions PASS, TECHNICALLY_CONFORMANT.
- hildibrand-dies: identical silence signature as R7 run
  (DamageAll FOREIGN only; roster shows Hildibrand in actor graveyard).

## Per-execution verdicts

1. kappa-etb-other (634a4b2d + 998516b9): EVIDENCED-CANDIDATE
   (promotion withheld: batch gate unsealed).
2. gateway-etb-other (998516b9 shared): EVIDENCED-CANDIDATE, shared
   diversity valid, no new count (promotion withheld as above).
3. hildibrand-dies (2dd428f9): UNKNOWN + HARNESS_DEFECT, mechanism
   REFINED this session from pin source (see below). No engine defect.

## Root-cause refinement (CODE_DERIVED at FORGE_PIN, TriggerHandler:242-285)

- R8 drained the WRONG queue. runTrigger queues to the WAITING list
  only when (stack frozen || holdTrigger) (TriggerHandler:258); otherwise
  the trigger runs IMMEDIATELY into SIMULTANEOUS stack entries
  (TriggerHandler:261), which reach the real stack ONLY via
  MagicStack.addAllTriggeredAbilitiesToStack.
- runWaitingTriggers() returns false on an empty waiting list
  (TriggerHandler:272-276): R8's drain no-oped while Hildibrand's dies
  trigger sat simultaneous-pending. This matches drivePostTravelStack's
  own comment (three states: simultaneous-pending / on-stack /
  auto-resolved) — the fixture path covered only the waiting list.
- SBA kill itself is engine-correct (graveyard proof stands).

## Partition (unchanged)

- 11 EVIDENCED / 689 UNKNOWN retained. No promotion from an unsealed
  batch (batch-2 precedent).

## Evidence classification

- Run/job/artifact/diagnostic/record bytes: DIRECTLY_VERIFIED.
- Waiting-vs-simultaneous queue mechanism: CODE_DERIVED (pin
  TriggerHandler + MagicStack + driveWaitingTrigger/drivePostTravelStack
  patterns already in-harness).
- No new promotions from this run.

## Exact next action (R9, generic harness-only)

Dual-queue drain in clearStackAndSettle: per wave, first
addAllTriggeredAbilitiesToStack (simultaneous-pending) -> resolve+SBA
if stack non-empty, else runWaitingTriggers (waiting list) -> move +
resolve+SBA; exit when both empty; bounded 8, fail-closed on excess.
Mirrors drivePostTravelStack's triple-cover. Digest-neutral (no
definitions/workflow/consultation changes). Then gates -> commit/push ->
PENDING -> replacement run.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
