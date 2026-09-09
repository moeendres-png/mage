# WS33-C Batch 4 R8-fix run PENDING

RUN = 34405294947
JOB = 102646709421
EVENT = push
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
SOURCE_HEAD = 4f33837d7286a49ef4c4b5eabef603ccc5d7e68a
SOURCE_TREE = 899caadd06e9fab1a9770294e1268cb108d6d8ca
BATCH_ID = WS33_C_BATCH_4
BATCH_DIGEST = b9aa07cec3b284ea75bada8b75f1a33b98c286daa7fc9717f64d0e76f39cacd0
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
DIRECT_RUNTIME_SOURCE_HEAD = d8af15cb879bdfc3c40ce4cba3462da24ee3f272
WS01_HEAD = bf089ea806f54a9bbb64ede205915729e3629684
WS12_HEAD = 80743bdbc2950b00e422f3deb38f04111f30a4d4
WS32_HEAD = 6ca2a7bbacd074cc84fa4a6019c4d26e5e3717a9
EXPECTED_ARTIFACT = ws33-c-abilitysub-batch-34405294947
EXPECTED_EXECUTIONS = 3 (kappa-etb-other, gateway-etb-other, hildibrand-dies)
EXPECTED_NEW_PATHS = 3 (634a4b2d sub-link; 998516b9 terminal shared;
2dd428f9 terminal MayPlay) + 1 shared diversity slot (gateway on 998516b9)
EXPECTED_GATE = generated/evidence/WS33_C_BATCH_GATE.json
R8_VS_PRIOR = bounded post-SBA waiting-trigger drain in clearStackAndSettle
(8 waves, fail-closed); digest-neutral (definitions/workflow untouched).
PRIOR = R7 run 34404564664 FAIL: kappa/gateway EVIDENCED-CANDIDATE records
PASS (promotion withheld, gate unsealed); hildibrand UNKNOWN +
HARNESS_DEFECT (post-SBA waiting trigger undriven; SBA kill proven).
Batch-2 PASS (11/689) retained; batch-3 EMPTY (scope boundary, no run).
COVERAGE_PROMOTION = FALSE
FREEZE = Run source frozen above. WRITE_FREEZE on batch inputs until terminal.

Terminal adjudication is per-path (EVIDENCED vs UNKNOWN+cause); workflow
green alone adjudicates nothing. PASS/FAIL persisted before any repair.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
