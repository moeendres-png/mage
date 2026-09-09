# WS33-C WAVE-001 dry-run exact diff report (staging only, NOT installed)

RECEIPT_ID = WS33_C_WAVE_001_DRYRUN_20260910
PROPOSAL = c-promotion/proposals/WS33_C_WAVE_001.json
PROPOSAL_DIGEST = 048b6502d1f5a4448f885e987fe3066a18fc34550f6a654e11d6acab5e7ae61e
TARGET = forge-behavior-v2:634a4b2d09d12a138afd0544c87c7d2bdb57a05a
WITNESS_ID = ws33-c-batch-5-634a4b2d
VALIDATOR_RESULT = WS33_WITNESS_VALIDATION=PASS (canonical abi validator, no C-specific validator)
EVIDENCE_CLASS = TECHNICALLY_CONFORMANT (preserved; never upgraded to ERV)
COVERAGE_PROMOTION_INSTALLED = FALSE

## Source lock (freshly verified 2026-09-10)

- C witness branch: work/ws33-c-high-throughput-20260907 @
  1f25789c6e75e9523bcd8d1b147161684214b26b (== expected; worktree
  /home/moeen/code/mage-ws33; clean; REMOTE-BACKED, origin matches).
- Serial base: work/ws33-serial-integration-af8-b-20260909 @
  c4ae1e0946f18045a817b8fb867fba10c2564b87 TREE
  d896866ec056cc96af70b9a3d9030fb80580ba45 (== expected; worktree
  /home/moeen/code/mage-ws33-int-af8b; REMOTE-BACKED: origin resolves,
  coordinator's unresolvable-tip note is stale, no remote provenance invented).
- Implementation branch (isolated, from serial tip, C branch untouched):
  work/ws33-c-dualbook-promotion-20260910 @ /home/moeen/code/mage-ws33-ws33c-promo.

## Retained evidence (all cross-checked, none re-witnessed)

- RUN 34410975075 / JOB 102665052139 /
  ARTIFACT 10127286824 /
  ARTIFACT_DIGEST sha256:d44de127ef7c75a00d3c7bee580aa0d0eed700cac6a61c86e5d65432d0358e8d
  (ZIP digest == GitHub digest == checkpoint; downloaded bytes verified).
- BATCH_DIGEST 9c0c153f8fe2f7a65e67cd12d3d32fa30797e6b41eb76c60002a7f877a05d72b.
- C SOURCE HEAD/TREE c03b8c5d4c75a5589723b91794494c14dac22939 /
  b3f85caf4cde9508404cb926e8ee4a71523dfb52 (objects exist; source descends
  from approved qualification source f2ae96970d8f9ce5df2dfd71782a1940be17b31d).
- C MANIFEST sha256 b47510017fbfd5cae478917c37f83c1a41e73095eb49a2fa9ecb43360c809ca4
  (== workflow C_MANIFEST_SHA256 declaration).
- C PARTITION sha256 4ccebd854556fbbed72584e391be8e79272488ddf83964868b114525d432642c
  (== PASS checkpoint PARTITION_SHA256).
- FORGE_PIN 8c7e9afb8e6caee88644b94e25da5852e36f8928 (bound in-run:
  `git -C forge rev-parse HEAD` check, 18/18 steps success; AbilitySub class
  existence proven by in-run compilation+execution against the pinned source;
  retained matched_link modeled == actual == forge.game.spellability.AbilitySub,
  IDENTICAL).
- Attribution: target NOT in WS33_C_ATTRIBUTION_DEFECT.json (345 entries) -> clean.
- rules_authority_refs preserved VERBATIM from retained record
  (603.3, 608.2); no reference added, none fabricated; TC not upgraded.

## Counts (assertions verified, not forced)

- Book A (WS33_PATH_COVERAGE.json, 4276): PASS 2 -> 3, UNKNOWN 4274 -> 4273.
- Book B (WS33_INTEGRATED_CLOSURE_LEDGER.jsonl, 4188): PASS 1152 -> 1153,
  UNKNOWN 3036 -> 3035. Frontier gate and work queue recomputed to match.

## Exact staged transitions (semantic)

- Book A: exactly {TARGET: UNKNOWN -> PASS}.
- Book B: exactly {TARGET: UNKNOWN -> PASS}.
- Promoted set equality: A == B == proposal set. Unrelated path changes: 0.
- Previous PASS sets unchanged in both books (2 Book-A IDs, 1152 Book-B IDs).

## Derived staged changes (deterministic recomputation, no semantics)

- Book A: status_counts; case scenario_status; exec status/source/trace/witness;
  per-identity pass/unresolved (identity stays PARTIAL, 1/9 -> 2/9 evidenced);
  scenario registry ws33-template-113 admitted += TARGET; target registry
  AbilitySub unproved 355 -> 354; Q6 counts/blockers/family gates; witnesses
  index += ws33-c-batch-5-634a4b2d (now 2 rows).
- Book B: queue regroup (3035 unresolved, 219 items); gate counts + ledger/
  queue shas + promotion_evidence_sha256.

## Guards proven (16/16 tests pass)

- Tampered gate / wrong source / empty rules refs / non-TC class / unapproved
  execution source / pre-state PASS all fail the adapter closed.
- Unknown ID -> IDENTITY_RECONCILIATION_REQUIRED; digest tamper ->
  PROPOSAL_DIGEST_MISMATCH; rerun on staged books ->
  DUPLICATE_ALREADY_PROMOTED (real books and synthetic); canonical install
  without WS33_C_ALLOW_CANONICAL_INSTALL=1 -> INSTALL_REFUSED.
- Restage with identical inputs is byte-identical (books + receipt).

## Canonical-install status

- NOT INSTALLED. Canonical ledgers byte-identical to serial base
  (git status clean for all tracked book files). Staged books live only under
  c-promotion/staging/ (untracked, regenerable). Install requires serial
  authority + WS33_C_ALLOW_CANONICAL_INSTALL=1 (never in dry-run).

## Regeneration (deterministic)

1. adapter (see c-promotion/adapted/ws33-c-batch-5-634a4b2d/adapter-mapping.json
   for the field-by-field basis) with the exact argv from shell history;
2. promoter stage with --receipt-id WS33_C_WAVE_001_DRYRUN_20260910;
3. python3 c-promotion/test_ws33_c_dualbook_promotion.py (16 tests).

## Stop-state flags

ARCHITECTURE_FREEZE = NOT CLAIMED
PRODUCTION_PROVIDER = NOT SELECTED
TASK WS33-C dry-run for 634a4b2d = COMPLETE (implementation + tests + staged
dry-run + receipt + this diff report). No Batch-6. No Full107. No push.
TURN_STATUS = INTERRUPTED (WS33 overall NOT complete)
TASK_COMPLETE = NO
