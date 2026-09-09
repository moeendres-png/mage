# WS33-C Batch 4 R7-fix run 34404564664 terminal FAIL (independently adjudicated)

RUN = 34404564664
JOB = 102644319063 (completed/failure)
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
WORKFLOW_SOURCE_HEAD = 67b85e427072a6e5b34c7050f9ca27737c6a3850
WORKFLOW_SOURCE_TREE = be5186794aaf47b7aba81bc0d8984fba81ff4979
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10124884687 (ws33-c-abilitysub-batch-34404564664)
BATCH_ID = WS33_C_BATCH_4
BATCH_DIGEST = b9aa07cec3b284ea75bada8b75f1a33b98c286daa7fc9717f64d0e76f39cacd0
GATE = generated/evidence/WS33_C_BATCH_GATE.json NOT PRODUCED (Record step:
2/3 markers; workflow requires 3)
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Independent verification (immutable artifact bytes, local 2026-09-09)

- Plan digest matches PENDING (b9aa07ce...); case_rows=4, path_slots=4.
- abilitysub-record-diagnostics.jsonl has exactly 1 row (hildibrand-dies).
- records/: kappa-etb-other + gateway-etb-other record-success.marker
  present; hildibrand-dies absent.

## Per-execution verdicts

1. kappa-etb-other: ALL RECORD ASSERTIONS PASS from raw record bytes
   (kappa-counters 2/2, kappa-static 2/2, hand -1/-1, after-eot 0/0 x2,
   both production-child-reached true). R7-1 (expected 1->2) and R7-2
   (CLEANUP rollback) VERIFIED in production. Links 634a4b2d + 998516b9
   observed exactly; evidence class TECHNICALLY_CONFORMANT in-record.
   Verdict: EVIDENCED-CANDIDATE (promotion withheld: batch gate unsealed).
2. gateway-etb-other: ALL PASS (gateway-static 1/1, hand -1/-1,
   after-eot 0/0, terminal reached true). Shared-terminal diversity slot
   independently valid (no new count). Verdict: EVIDENCED-CANDIDATE
   (shared; promotion withheld as above).
3. hildibrand-dies: `terminal root resolution not observed ... roster=
   [p2:Thunder Dragon|Hildibrand Manderville;p1:|]`.
   R7-3 diagnostics PROVED the mechanism: setup verification raised
   nothing (Hildibrand reached battlefield pre-fixture); Thunder
   DamageAll resolved x2 (foreign, correctly unattributed); Hildibrand
   is in actor graveyard (SBA destroy confirmed); its ChangesZone
   Battlefield->Graveyard Self dies trigger (card text at pin) therefore
   necessarily became WAITING, but was never moved to stack/resolved in
   the fixture window (clearStackAndSettle has no post-SBA waiting-
   trigger drain; only stack + SBA flush). No engine defect evidenced:
   damage, SBA kill, and graveyard placement all correct per pin Rules
   Core behavior.
   Root cause class: HARNESS_DEFECT (incomplete post-SBA waiting-trigger
   drain). Path 2dd428f9 verdict: UNKNOWN + HARNESS_DEFECT.

## Partition (unchanged)

- 11 EVIDENCED / 689 UNKNOWN retained. No promotion from an unsealed
  batch (batch-2 precedent: promotion only on full batch PASS with
  sealed gate + independent adjudication). kappa/gateway record bytes
  are preserved DIRECTLY_VERIFIED observations reusable at the next
  full PASS.

## Evidence classification

- Run/job/artifact/diagnostic/record bytes: DIRECTLY_VERIFIED.
- Hildibrand trigger-waiting inference: CODE_DERIVED (pin card text +
  pin TriggerHandler/clearStackAndSettle structure + graveyard proof).
- No new TECHNICALLY_CONFORMANT promotions from this run.

## Exact next action (R8, generic harness-only)

Bounded post-SBA waiting-trigger drain in clearStackAndSettle
(runWaitingTriggers -> addAllTriggeredAbilitiesToStack ->
playUntilStackClear + checkStateEffects, bounded 8, fail-closed on
excess; mirrors existing driveWaitingTrigger machinery; resolves only
what the engine already queued, matching still gates attribution).
No definitions/workflow/digest/consultation changes (digest-neutral).
Then focused gates -> commit/push -> PENDING -> replacement run.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
