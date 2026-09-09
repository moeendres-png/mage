# WS33-C Batch 4 run PENDING

RUN = 34385344654
EVENT = push
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
SOURCE_HEAD = 29fbd77fb052e03af2c01329dd5097d2fa78f551
SOURCE_TREE = 489500301292c8faeadfb1c574f4e94d065e3490
BATCH_ID = WS33_C_BATCH_4
BATCH_DIGEST = a294312c2015696e8e22131e3071368951be5c07e4fdc43757543116055983de
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
EXPECTED_ARTIFACT = ws33-c-abilitysub-batch-34385344654
EXPECTED_EXECUTIONS = 3 (kappa-etb-other, gateway-etb-other, hildibrand-dies)
EXPECTED_NEW_PATHS = 3 (634a4b2d sub-link; 998516b9 terminal shared;
2dd428f9 terminal MayPlay) + 1 shared diversity slot (gateway on 998516b9)
EXPECTED_GATE = generated/evidence/WS33_C_BATCH_GATE.json
NEW_MACHINERY = effect_static_present assertions (+after_eot_absent EOT
rollback phase); settleSetup drain; StaticAbilityMode allowlist; aspect-dual
credit (linkage + content aspects share one observed pair, distinct ids).
COVERAGE_PROMOTION = FALSE
PRIOR = batch-2 PASS (11/689); batch-3 EMPTY (scope boundary, no run)
FREEZE = Run source frozen above. WRITE_FREEZE on batch inputs until terminal.

Terminal adjudication is per-path (EVIDENCED vs UNKNOWN+cause); workflow
green alone adjudicates nothing. PASS/FAIL persisted before any repair.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
