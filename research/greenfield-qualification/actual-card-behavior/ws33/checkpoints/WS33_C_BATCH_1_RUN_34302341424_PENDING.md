# WS33-C Batch 1 R6 run PENDING

RUN = 34302341424
EVENT = push
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
SOURCE_HEAD = c5138033796dcb42f86b514a97bca878a09f66ed
SOURCE_TREE = 6fafcfde8baf7caa771eeb1db0839c9e56a8dbee
BATCH_ID = WS33_C_BATCH_1 (R6 revision)
BATCH_DIGEST = 2adfe66ef6bbfb99d9bdb21580587a9e878f3cb78ac7c60d4eeba31c091c462d
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
EXPECTED_ARTIFACT = ws33-c-abilitysub-batch-34302341424
EXPECTED_EXECUTIONS = 7 (cloudblazer-etb-rewitness, rager-etb,
shimmercreep-etb, bane-etb, chopper-etb, cap-hero-etb, armor-etb)
EXPECTED_NEW_PATHS = 7 (ed6d9d36, 067886a9, 2f542f51, c01749f7, 8d18d77c,
746c658d, 494de427) + pilot re-witness + 2 shared diversity slots
EXPECTED_GATE = generated/evidence/WS33_C_BATCH_GATE.json
IMMUTABLE_DEPS = owned manifest b4751001…; partition f1003eb3… (1 evidenced);
selection WS33_C_BATCH_1_SELECTION.md; attribution artifact 72f21c56…
R6_CHANGES_VS_R5 = pair-matching by object relation; snapshot-after-hand;
checker screen gate (Mode TgtChoose + Dig rules); armor diversity;
gnarlbark deferred (FIXTURE_INFRASTRUCTURE_PENDING); workflow digest/rows.
COVERAGE_PROMOTION = FALSE
PRIOR = 34299361792 FAIL (duplicate inert proven, silent EOT open; adjudicated)
FREEZE = Run source frozen above. WRITE_FREEZE on batch inputs until terminal.

Terminal adjudication is per-path (EVIDENCED vs UNKNOWN+cause); workflow
green alone adjudicates nothing. PASS/FAIL persisted before any repair.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
