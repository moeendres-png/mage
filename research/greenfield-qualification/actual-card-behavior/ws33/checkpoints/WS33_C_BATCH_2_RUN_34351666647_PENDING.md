# WS33-C Batch 2 R7 run PENDING

RUN = 34351666647
EVENT = push
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
SOURCE_HEAD = 437596b0574e92394b74e6508fe59bcf0f105727
SOURCE_TREE = 7c2eb963a499e72e8f57dca7df6e4ce935d9fc8a
BATCH_ID = WS33_C_BATCH_2 (R7 revision)
BATCH_DIGEST = 9845779cbfd430b52008c2888d677866d81f74e45224c1ff712e29624f4a1e15
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
EXPECTED_ARTIFACT = ws33-c-abilitysub-batch-34351666647
EXPECTED_EXECUTIONS = 5 (gnarlbark-eot, thunder-etb, ironsmith-upkeep,
banshee-upkeep-own, snuffers-etb)
EXPECTED_NEW_PATHS = 3 (2c49adc7 DBBlight sub-link; 7574de05 terminal shared;
a4f6a646 terminal transform) + 2 shared diversity slots
R7_CHANGES_VS_FAILED_RUN = gnarlbark declared forced-choice consultation
(Blight singleton, source-verified); tripwire actor capture; reference
object-identity attribution (no mutable names); SBA settle after stack
clear; roster+damage diagnostics; forced-choice bundles; certifier
normalization + 22 self-tests. No shared Decision infra touched.
COVERAGE_PROMOTION = FALSE
PRIOR = 34307846206 FAIL (3 causal branches adjudicated from immutable
artifact; coordinator ModuleNotFoundError finding CONTRADICTED by evidence:
materialization succeeded, tests ran)
FREEZE = Run source frozen above. WRITE_FREEZE on batch inputs until terminal.

Terminal adjudication is per-path (EVIDENCED vs UNKNOWN+cause); workflow
green alone adjudicates nothing. Banshee/snuffers prior candidate records
stay preserved immutable; this run regenerates upgraded evidence for all 5.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
