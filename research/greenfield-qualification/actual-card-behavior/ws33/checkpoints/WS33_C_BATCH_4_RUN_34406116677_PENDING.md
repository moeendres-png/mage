# WS33-C Batch 4 R9-fix run PENDING

RUN = 34406116677
JOB = 102649380734
EVENT = push
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
SOURCE_HEAD = d26be3b06c57e0d5a28ea5ef003621c3fc1639f1
SOURCE_TREE = 26378e0a25d684dc0babd7732ab71e18622dd2e3
BATCH_ID = WS33_C_BATCH_4
BATCH_DIGEST = b9aa07cec3b284ea75bada8b75f1a33b98c286daa7fc9717f64d0e76f39cacd0
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
DIRECT_RUNTIME_SOURCE_HEAD = d8af15cb879bdfc3c40ce4cba3462da24ee3f272
WS01_HEAD = bf089ea806f54a9bbb64ede205915729e3629684
WS12_HEAD = 80743bdbc2950b00e422f3deb38f04111f30a4d4
WS32_HEAD = 6ca2a7bbacd074cc84fa4a6019c4d26e5e3717a9
EXPECTED_ARTIFACT = ws33-c-abilitysub-batch-34406116677
EXPECTED_EXECUTIONS = 3 (kappa-etb-other, gateway-etb-other, hildibrand-dies)
EXPECTED_NEW_PATHS = 3 (634a4b2d sub-link; 998516b9 terminal shared;
2dd428f9 terminal MayPlay) + 1 shared diversity slot (gateway on 998516b9)
EXPECTED_GATE = generated/evidence/WS33_C_BATCH_GATE.json
R9_VS_PRIOR = dual-queue drain in clearStackAndSettle: simultaneous-pending
via addAllTriggeredAbilitiesToStack first, then waiting list via
runWaitingTriggers; exit when both empty; bounded 8, fail-closed.
Digest-neutral (definitions/workflow untouched).
PRIOR = R8 run 34405294947 FAIL: kappa/gateway EVIDENCED-CANDIDATE records
PASS (promotion withheld); hildibrand UNKNOWN + HARNESS_DEFECT refined to
simultaneous-pending queue (R8 drained waiting list only; pin
TriggerHandler:258-285 proves the split). Batch-2 PASS (11/689) retained.
COVERAGE_PROMOTION = FALSE
FREEZE = Run source frozen above. WRITE_FREEZE on batch inputs until terminal.

Terminal adjudication is per-path (EVIDENCED vs UNKNOWN+cause); workflow
green alone adjudicates nothing. PASS/FAIL persisted before any repair.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
