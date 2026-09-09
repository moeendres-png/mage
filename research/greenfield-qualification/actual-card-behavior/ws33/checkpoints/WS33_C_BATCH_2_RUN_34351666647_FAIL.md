# WS33-C Batch 2 R7 run 34351666647 terminal FAIL (adjudicated)

RUN = 34351666647
JOB_CONCLUSION = failure (step "Execute batch Record", test compilation)
SOURCE_HEAD = 437596b0574e92394b74e6508fe59bcf0f105727
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = ws33-c-abilitysub-batch-34351666647 (overlay + materialization logs)
FAILURE = Ws33AbilitySubWitnessTest.java:[171,25] cannot find symbol
  (sourceRef used in setup loop before its declaration site).
COVERAGE_PROMOTION = FALSE

## What passed (DIRECTLY_VERIFIED from run log)

Manifest binding, pins, all overlays (incl. actor-capture tripwire v2),
batch materialization (digest 9845779c, 5 rows), test install.

## Root cause (HARNESS DEFECT, C-local, compile-time)

Declaration-order slip when introducing the sourceRef holder: setup block
references it before the `final Card[] sourceRef` declaration. No engine,
overlay, model, or witness-design issue. Repair: declare before setup.

EVIDENCED_PATH_COUNT = 8 (unchanged, Batch-1 retained)
REMAINING_UNKNOWN_COUNT = 692 (unchanged)

## Exact next action

Commit FAIL + one-spot declaration fix, push (replacement run, same
digest), PENDING, per-path adjudication, repartition.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
