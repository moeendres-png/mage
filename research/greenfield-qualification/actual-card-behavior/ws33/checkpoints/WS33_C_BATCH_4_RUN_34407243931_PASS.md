# WS33-C Batch 4 R10-fix run 34407243931 terminal PASS (independently adjudicated)

RUN = 34407243931
JOB = 102653063171 (completed/success)
WORKFLOW = WS33-C AbilitySub batch witness (production-parent)
WORKFLOW_SOURCE_HEAD = 8271743ea113ae2e5d8d1a3967f744566159d96b
WORKFLOW_SOURCE_TREE = 29c2a058863d00b429cd7c1256a1f9ffac1fecb0
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10125902030 (ws33-c-abilitysub-batch-34407243931)
ARTIFACT_DIGEST = sha256:760ed2d6174ad3dd3ab686a47286a99c0353c8fdcf15c6cbdb9fc49355e6e181
(ZIP digest == GitHub digest, verified locally)
BATCH_ID = WS33_C_BATCH_4
BATCH_DIGEST = b9aa07cec3b284ea75bada8b75f1a33b98c286daa7fc9717f64d0e76f39cacd0
GATE = generated/evidence/WS33_C_BATCH_GATE.json status EVIDENCED x2 + UNKNOWN x1 (in-workflow)
DIAGNOSTICS = empty (0 bytes); markers 3/3; all evidence file hashes OK
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE

## Independent verification (artifact bytes; batch-2 rigor, green workflow adjudicates nothing)

1. gateway-etb-other -> forge-behavior-v2:998516b92a13efe9c0e1c324a8123069ab954815
   Terminal Unblockable root, EVIDENCED. Trace v2, pin/batch/exec/oracle/
   source/fixture identity exact; production entrypoint AbilityUtils.
   resolve, stack path trigger->MagicStack->AbilityUtils.resolve->
   AbilitySub.resolve; terminal pair (41,41) child-entry seq 2 <
   parent-return seq 3, parentId -1, root==id, host_is_fixture_source
   true on both, TERMINAL==TERMINAL, modeled==actual AbilitySub,
   IDENTICAL; Gruul Tap outlet foreign/unattributed; static count 1
   CantBlockBy/linked/controller-actor + after-eot 0/0 (CLEANUP rollback
   proven); 4/4 assertions PASS with plan values; tripwire exact 7-method
   set, 2 hits all incidental; profile clean; no direct resolution.
   Path pre-run UNKNOWN, template-113, STATE_ONLY, AbilitySub target.
2. hildibrand-dies -> forge-behavior-v2:2dd428f906c3201282d1e251a9daf937f3413b94
   Terminal MayPlay root, EVIDENCED. Same identity/entrypoint rigor;
   terminal pair (71,71) child seq 3 < parent seq 4, host_is_fixture_
   source true on both VIA the pin-proven piece-ID bridge (graveyard
   copy carries the placed card's ID); id=72 envelope parent
   unattributed (no child) per standing rule; Thunder DamageAll foreign/
   unattributed (already evidenced, not claimed); static count 1
   Continuous+MayPlay/linked/controller-actor; graveyard 1/1, hand -1/-1;
   4/4 assertions PASS; tripwire 4 hits all incidental; profile clean.
   Path pre-run UNKNOWN, template-113, STATE_ONLY, AbilitySub target.
3. kappa-etb-other -> forge-behavior-v2:634a4b2d09d12a138afd0544c87c7d2bdb57a05a
   sub-link pair (20,21) exactly matched BUT static observation count=2
   shared across setup + fixture firings and unmappable to the pair from
   record bytes. In-workflow certifier fail-closed UNKNOWN ("effect-
   static observation not unique") CONCURRED independently. Verdict:
   UNKNOWN + FIXTURE_DEFECT (shared-execution design). Remedy: solo
   via=place re-witness (direct placement fires no entry trigger ->
   count 1, unique) as batch-5 candidate. No engine/harness defect.

## Partition (branch-owned, not canonical)

- WS33_C_EVIDENCE_PARTITION.json regenerated deterministically:
  EVIDENCED_PATH_COUNT = 13 (11 retained + 2 new)
  REMAINING_UNKNOWN_COUNT = 687
- Canonical WS33_PATH_COVERAGE.json untouched (all three paths stay
  UNKNOWN there until serial cross-qualification promotes).

## Evidence classification

- Run/job/artifact/digest/hash/seq/id/relation/state/actor observations:
  DIRECTLY_VERIFIED.
- addUntilCommand/CLEANUP expiry, trigger queues, copy-on-leave + ID
  preservation, trigger-host chain: CODE_DERIVED from pin source.
- 998516b9 + 2dd428f9 bounded production-linked executions:
  TECHNICALLY_CONFORMANT. No EXTERNALLY_RULE_VALIDATED upgrade claimed.
- 634a4b2d: UNKNOWN (above). No waivers, no manual injection, no name
  gating, no shared-Decision changes.

## Exact next action

Commit PASS + repartition, push; then final WS33-C handoff (retained
11/689 -> 13/687 accounting, R7/R8/R9/R10 chain, batch-5 solo kappa
candidate, WRITE_FREEZE lifted for C batch inputs only after this push).

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
