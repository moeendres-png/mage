# WS33B coverage-promotion proposal (B1 + B2) — for the canonical/integration line

Status: PROPOSAL_ONLY. This B branch does NOT own canonical coverage/identity
registries and performs no promotion itself. Serial deterministic promotion,
if accepted, must execute on the canonical/integration line with its own
PENDING -> PASS/FAIL checkpoint discipline (COVERAGE_PROMOTION=FALSE here).

## Immutable inputs

- B1: run 34266311850, job 102196461658, artifact 10072131808
  (sha256:118de4169ae9abf4ab500213430a62cd67630d44cb9b34ce3032a93907a29c2f),
  source 80bc5fa2b2f99d2b763ab09d4194370ba631ca91, gate PASS, 273 paths.
- B2: run 34286249888, job 102262427048, artifact 10079683394
  (sha256:a8a498f63a776a772a78d531b21ffc1542c59bb218f10185f135271078aa00b3),
  source c0b8c57e7e29b7620ddf27ec768f29d1619460b7, gate PASS, 397 paths.
- Forge pin 8c7e9afb8e6caee88644b94e25da5852e36f8928 (both runs).
- Model: manifest cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224
  (4188), consumer 82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48.

## Proposed transitions (all UNKNOWN -> PASS)

- 267 B1 paths: EXTERNALLY_RULE_VALIDATED (positive amount evidence).
- 6 B1 paths: TECHNICALLY_CONFORMANT + default_zero_evidence + review_required
  DEAD_EXPRESSION (fail-closed engine defaults; EXCLUDE from promotion unless
  the successor explicitly adjudicates the flag — see
  WS33B_B1_DEFAULT_ZERO_ADJUDICATION_20260908.md).
- 397 B2 paths: EXTERNALLY_RULE_VALIDATED (positive payment evidence).
- Union B1+B2: 670 paths, pairwise disjoint, disjoint from the 285 base PASS
  (verified: all overlaps 0).
- 5 Cost terminal blockers remain UNKNOWN (exact IDs in
  WS33B_COST_TERMINAL_BLOCKERS_20260908.md); they are NOT proposed.

## Expected successor counts (if 664 positive paths promoted, defaults held)

- PASS: 285 + 664 = 949; UNKNOWN: 3700 - 664 = 3036 (per operational base
  TOTAL=4188 PASS=488 UNKNOWN=3700 — NOTE: successor must recompute against
  the live canonical operational state, not this proposal's cached base).
- WS33B UNKNOWN: 675 - 664 = 11 (5 terminal + 6 held defaults).

## Successor preconditions (checklist for the canonical worker)

1. Re-verify live canonical HEAD/TREE and operational state.
2. Confirm B1/B2 artifact digests above against live GitHub.
3. Confirm disjointness against live PASS set (recompute, do not trust this file).
4. Decide the 6 default-zero paths (promote as TECHNICALLY_CONFORMANT or hold UNKNOWN).
5. Persist PENDING with frozen source before any registry mutation.
6. Mutate serially, recompute derived registries, adjudicate gates, persist PASS/FAIL.

## Classification

DIRECTLY_VERIFIED (artifact/run/job/digest/disjointness facts).
No coverage register was modified by this proposal.
