# WS33-C Batch 1 run 34303271838 terminal PASS (independently adjudicated)

RUN = 34303271838
JOB = 102311731216 (completed/success)
WORKFLOW_SOURCE_HEAD = 4dbf271a5a
WORKFLOW_SOURCE_TREE = (see workflow-source-tree.txt in artifact)
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10085761926 (ws33-c-abilitysub-batch-34303271838)
ARTIFACT_DIGEST = sha256:171b71748df610b434f38fdbd7e641fc6f4007fc3c0e5b2a3b0eee3cbce9db3e
BATCH_DIGEST = 2adfe66ef6bbfb99d9bdb21580587a9e878f3cb78ac7c60d4eeba31c091c462d
GATE = generated/evidence/WS33_C_BATCH_GATE.json status PASS (in-workflow)
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Independent verification (artifact ZIP digest == GitHub digest; 29/29 hashes)

For each of 7 executions, verified from raw record/trace bytes:
- schemas (record v1, trace v2), forge pin, batch/execution identity,
  oracle singleton, exact v2_path_ids set, marker present;
- execution boundary (rules-core true, silent 0, direct false,
  decision NOT_REQUIRED), TECHNICALLY_CONFORMANT;
- exact chain: integer parent_seq < child_seq on matched ids,
  child.parent_id == parent.id, root linkage, runtime-derived relation ==
  declared child_sub == manifest selector, modeled == actual ==
  forge.game.spellability.AbilitySub with explicit IDENTICAL relation;
- tripwire: exact 7-method set; every hit incidental (mainLoopStep caller)
  except declared singleton consultations (AttachEffect caller, options=1)
  in chopper/armor, each observed exactly;
- profile flags all clean, replay not required;
- every planned semantic assertion result PASS with plan-expected value;
- per-link production-child-reached present;
- each path UNKNOWN in canonical coverage, template-113, STATE_ONLY dims.

Per-path verdicts: 7 NEW EVIDENCED (ed6d9d36, 067886a9, 2f542f51, c01749f7,
8d18d77c, 746c658d, 494de427) + pilot b42b594f re-witnessed under the v2
contract (upgrades its order evidence to observed) + 2 shared-path
diversity witnesses (armor parents for 8d18d77c/746c658d).

## Audit-gap closure status (Sol addendum items 2-6)

- Item 2 (trace integrity, option A): parent-resolution hook live;
  ordering verified from recorded integer seqs per matched chain. CLOSED
  for this witness shape.
- Item 3 (exact chain): ids (parent/child/root), object relation,
  runtime-derived SubAbility relation, host, provenance, modeled/actual
  classes + relation — all recorded and certified per link. CLOSED.
- Item 4 (semantic completeness): per-case effect-specific assertions
  (life/hand/counts/counters/keywords/equip), all PASS; Kappa-class
  Effect-statics left UNKNOWN/WITNESS_ASSERTION_INFRASTRUCTURE_PENDING.
  CLOSED for batch scope.
- Item 5 (runtime profile): tripwire (7 methods, caller-attributed) +
  structural screen + exact postconditions per record. CLOSED.
- Item 6 (negatives): predicate + object-level direct-child negatives
  green in-run; certifier self-test 15/15. CLOSED.
- Item 1 (scope cap): honored (template-113 only; 105/119 untouched).
- Item 7 (pilot): uninvalidated; re-witnessed stronger.

## Partition (branch-owned, not canonical)

- WS33_C_EVIDENCE_PARTITION.json sha256
  4b7b9ac14c3da75d5acb1d61140f596028bdd3038ccbb6581386b49209820b09
- EVIDENCED_PATH_COUNT = 8 (7 new + pilot)
- REMAINING_UNKNOWN_COUNT = 692 (STATE_ONLY remaining 297, incl. 129 in
  scope-capped 105/119; decision/hidden/RNG infra-pending 395)
- Gnarlbark DBBlight path stays UNKNOWN/FIXTURE_INFRASTRUCTURE_PENDING.

## Evidence classification

- run/job/artifact/digest/hash/seq/id/relation/state observations:
  DIRECTLY_VERIFIED.
- Production nesting (wrapper/inner) mechanism: CODE_DERIVED from pin source.
- Bounded actual-card production-linked executions: TECHNICALLY_CONFORMANT
  as recorded. No EXTERNALLY_RULE_VALIDATED upgrade claimed (no independent
  official-rules input).

## Exact next action

Batch-2 selection from remaining template-113 STATE_ONLY: rank next
fixture classes (targeted-ETB with authoritative target protocol vs
Effect-static vocabulary vs phase-family investigation); persist selection;
definitions; PENDING; run; adjudicate; repartition. Batch-1 machinery
(preparer/checker/harness/certifier/workflow) reuses unchanged.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
