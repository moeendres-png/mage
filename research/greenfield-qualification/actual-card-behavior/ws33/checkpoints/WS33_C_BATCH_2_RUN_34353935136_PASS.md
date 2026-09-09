# WS33-C Batch 2 R7-fix run 34353935136 terminal PASS (independently adjudicated)

RUN = 34353935136
JOB = 102473725177 (completed/success)
WORKFLOW_SOURCE_HEAD = b6088fe238
WORKFLOW_SOURCE_TREE = (see workflow-source-tree.txt in artifact)
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10105006299 (ws33-c-abilitysub-batch-34353935136)
ARTIFACT_DIGEST = sha256:37ad31bc3c1e448b57d4843937097eca8c544e9a762a6630c11c945a1416cd50
BATCH_ID = WS33_C_BATCH_2 (R7 revision)
BATCH_DIGEST = 9845779cbfd430b52008c2888d677866d81f74e45224c1ff712e29624f4a1e15
GATE = generated/evidence/WS33_C_BATCH_GATE.json status PASS (in-workflow)
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Independent verification (artifact ZIP digest == GitHub digest; 23/23 hashes)

For each of 5 executions, verified from raw record/trace bytes (same rigor
as Batch-1, plus R7 elements):
- schemas, forge pin, batch/execution identity, oracle singleton, exact
  path-id sets, markers; execution boundary; TECHNICALLY_CONFORMANT.
- exact chain: integer ordering on matched ids (sub: parent<child;
  terminal: child-entry<parent-return), child.parentId linkage (sub-links),
  same-object terminal pairs, runtime-derived relation == declared,
  modeled == actual AbilitySub with IDENTICAL relation.
- STABLE OBJECT IDENTITY: host_is_fixture_source true on every matched
  pair member. Ironsmith pair proves it across transform: child host
  "Village Ironsmith" + parent host "Ironfang", same object reference.
  Mutable names recorded only, never gating.
- forced-choice bundle (gnarlbark): site chooseSingleEntityForEffect,
  options 1, actor p2 == initial.actor_name, caller BlightEffect.resolve,
  offered==selected==Sinister Gnarlbark, FORCED_SINGLETON, no external
  pilot, no fallback; selected covered by PASS M1M1 counter assertion.
- tripwire: exact 7-method set; all non-declared hits incidental
  (mainLoopStep callers); zero unexpected.
- profile flags all clean; every planned assertion PASS with plan value.
- each path UNKNOWN in canonical coverage, template-113, STATE_ONLY dims.

Per-path verdicts: 3 NEW EVIDENCED (2c49adc7 DBBlight sub-link;
7574de05 terminal DamageAll shared x65; a4f6a646 terminal Transform) +
2 shared diversity slots (banshee/snuffers on thunder's path, independently
valid, no double count).

## Causal-branch resolutions (from run 34307846206 adjudication)

- Gnarlbark: declared forced singleton, observed exactly, bundle complete.
- Thunder: SBA flush moved bear to graveyard (bear-gone 0, bear-graveyard
  1); damage path proven, no Rules-Core defect. Fixture/timing class.
- Ironsmith: reference-identity attribution; transform proven same-object.
- Coordinator ModuleNotFoundError finding CONTRADICTED by immutable
  evidence (materialization succeeded, tests ran); recorded as superseded.

## Evidence classification

- run/job/artifact/digest/hash/seq/id/relation/state/actor observations:
  DIRECTLY_VERIFIED.
- Production nesting + Blight consultation pattern + transform identity:
  CODE_DERIVED from pin source.
- Bounded actual-card production-linked executions: TECHNICALLY_CONFORMANT
  as recorded. No EXTERNALLY_RULE_VALIDATED upgrade claimed.

## Partition (branch-owned, not canonical)

- WS33_C_EVIDENCE_PARTITION.json sha256
  0cced9d2dcbc375da2b777cb814a1a8afca0afd56721ad80a38e83cc0ed2674d
- EVIDENCED_PATH_COUNT = 11 (8 retained + 3 new)
- REMAINING_UNKNOWN_COUNT = 689 (STATE_ONLY remaining 294)

## Exact next action

Batch-3 selection from remaining template-113 STATE_ONLY using proven
machinery (terminal matching, phase travel, forced-choice bundles,
reference identity): candidates biogenic-EOT combo (same shared terminal),
banshee/snuffers already cover shared path; new unique paths from
PutCounterAll-Upkeep/EOT variants, Kappa-class pending assertion vocab,
phase-silence family closed for EOT/upkeep-opp/own. Persist selection;
definitions; PENDING; run; adjudicate.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
