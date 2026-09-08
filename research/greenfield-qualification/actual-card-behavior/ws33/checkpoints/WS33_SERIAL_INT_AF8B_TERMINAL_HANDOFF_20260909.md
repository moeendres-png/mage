# WS33 serial integration (AF8 -> B) — TERMINAL HANDOFF for Sol High adjudication

Date: 2026-09-09. Branch: `work/ws33-serial-integration-af8-b-20260909` (isolated worktree/branch; no source workstream branch modified; no force-push; history linear).
Status: INTEGRATION COMPLETE, ADJUDICATION PENDING. This branch is a serial integration successor/candidate, NOT final canonical. No Architecture Freeze claimed.

## Source Lock

- BASE_CANONICAL_HEAD = `6da237b704ba5e66c58c2334f47e36ef68ca980d`, BASE_CANONICAL_TREE = `8f6d0151e4a9095c95925d6f6065214d382bf1dc` (== live `origin/work/ws33-g3-final-closure-20260902`, unmoved).
- AF8_SOURCE_HEAD = `1922a5172f0e004dd95c279744c641775a80b15a`, AF8_SOURCE_TREE = `ef71c0d06398dd4ae760ccf5cef69264b1b02fa6` (== live AF8 branch, unmoved; exactly 6 ahead/0 behind base; HEAD in integration ancestry).
- B_SOURCE_HEAD = `2c6ceedebb250165893d942251acf7550346c405`, B_SOURCE_TREE = `e352588fad89977b4fbd98824e4b3872dc3bd41a` (== live B branch, unmoved).
- FORGE_PIN = `8c7e9afb8e6caee88644b94e25da5852e36f8928`; manifest `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`; consumer `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`; B1 target digest `30dd81f733e0c1dfdb2d3020c0b9b1e0a2ed542fcf78123d641839fb24800024` (reproduced).
- No SOURCE_LOCK_DEFECT at any phase. C/A/D/E/F untouched (C at `ada567e664e679dccb84dea07fb00de198880ba6`, not incorporated).

## Work Completed

1. Phase I: dedicated worktree + branch from exact canonical base; all source locks/ancestry/GH run states re-verified; stale metadata recorded; PENDING-free checkpoint committed.
2. Phase II: AF8 repair integrated fast-forward-equivalent (linear history, no manual recreation); run 34222323657 SUCCESS re-verified with artifact gate (8 paths/0 failures/coverage unmutated) and in-artifact source binding; impact analysis => no rerun; checkpoint committed + pushed.
3. Phase III: B proposal precheck recomputed from immutable artifacts: 267 B1 + 397 B2 positive (all EXTERNALLY_RULE_VALIDATED), pairwise disjoint, all UNKNOWN in BOTH branch (285-PASS) and operational (488-PASS) states, disjoint from both PASS sets, queue bindings exact (B1 item == 273; Cost union == 397+5).
4. Phase IV: PENDING checkpoint with frozen source/evidence/sets/digests committed + pushed BEFORE any registry mutation.
5. Phase V: authoritative `ws33_promote_b_frontier.py` (G3/A1-pattern mechanism) promoted EXACTLY the 664; staged outputs independently re-verified; installed + committed.
6. Phase VI: counts recomputed; PROJECT_STATE.md + operational state reconciled to live state.
7. Phase VII: increasing-cost gates (ancestry, schema, conservation, derived consistency, held sets, no stray incorporation, AF8 inheritance, focused tests) all PASS.

## New Findings

- Branch-level ledger/queue/gate at canonical base read 285/3903 (not the metadata-claimed 488/3700): the G3/A1 promotion lives operationally in immutable artifact 9979204198 (verified: 488 PASS inside) while branch coordination files were left at 285/3903 and declared superseded. Recorded as known stale metadata; promotion base used is the live branch ledger; operational layer reconciled explicitly.
- B proposal cached math mixes bases and its disjointness covered only the 285 PASS set; this integration recomputed both layers and verified against the full 488 operational PASS set (overlap 0).
- The six default-zero IDs map exactly to the adjudicated cards (Estinien x2, Kemba's Legion, Exsanguinate, Hoarder's Greed, Inferno Trap) via ledger provenance.
- Integrated-ledger precedent (G3/A1) leaves tape refs null for externally-certified promotions; followed (witness_id + trace_sha256 bound per row instead); no 26MB evidence copy into git.

## Changes (vs canonical base; no C/A/D/E/F files)

- Inherited AF8 range (6 commits, verbatim): AF8 workflow repair, bounded-number overlay, hardener, contract test, Terra doc, AF8 checkpoints.
- Integration commits: 4 (reconciliation, AF8 checkpoint, PENDING, promotion) + terminal (PROJECT_STATE, operational state, this handoff).
- Mutated registries: WS33_INTEGRATED_CLOSURE_LEDGER.jsonl, WS33_INTEGRATED_WORK_QUEUE.json, WS33_INTEGRATED_FRONTIER_GATE.json (+ new WS33_POST_AF8B_PROMOTION_EVIDENCE.json, ws33_promote_b_frontier.py, promotion index, 5 checkpoints).

## Tests / Evidence

- `ws33_promote_b_frontier.py` internal gates: PASS (949/3239, B_UNKNOWN=11, residuals exact).
- Independent staged-output audit: 664 transitions == authorized set, all UNKNOWN->PASS, zero out-of-scope/non-transition changes, SHAs verify: PASS.
- Final live-tree validation (counts/shards/held/queue-union/gate-SHAs/operational consistency): ALL GATES PASS.
- test_ws33_integrated_successor.py: PASS. py_compile promote script: OK. All changed JSON/JSONL parse: OK.
- No B1/B2/AF8 workflow reruns (no invalidation; forbidden reassurance reruns not performed).

## PASS / FAIL / UNKNOWN

- AF8 integration: PASS (DIRECTLY_VERIFIED inheritance).
- B promotion (664): PASS (DIRECTLY_VERIFIED recomputation + gates).
- Six defaults + five blockers: UNKNOWN (held per Sol High; fail-closed, not functional support).
- WS33 overall: NOT COMPLETE (3239 UNKNOWN remain across A/B/C/D/E/F/G).

## Remaining Blockers

- Sol High adjudication of this successor before canonical promotion (no Freeze claimed here).
- Future serial qualifications: A-rest (incl. 6 defaults only with engine support/negative-evidence path), B residual 11 (incl. 5 blockers only with engine support), C 700, D 920, E 1029, F 319, G 81.

## Outputs

- Branch `work/ws33-serial-integration-af8-b-20260909` pushed (all milestones persisted; no working-tree-only state).
- Checkpoints: SOURCE_RECONCILIATION, AF8_INTEGRATION, B_PROMOTION_PENDING, this TERMINAL_HANDOFF + WS33_ABC_B1_B2_PROMOTION_INDEX + WS33_POST_AF8B_PROMOTION_EVIDENCE.json.

## Dependencies Unblocked

- A serially-integrated AF8+B-positive line for the next wave (C or A-rest) without re-proving AF8/B1/B2.

## Exact Next Action

- Sol High: adjudicate this successor (verify locks/counts/sets/digests from this handoff against the branch); on acceptance, promote `work/ws33-serial-integration-af8-b-20260909` as the new canonical line. NEXT_SERIAL_INTEGRATION_ACTION = none on this branch without a new PENDING freeze.

## Machine fields

BRANCH = work/ws33-serial-integration-af8-b-20260909
BASE_CANONICAL_HEAD = 6da237b704ba5e66c58c2334f47e36ef68ca980d
BASE_CANONICAL_TREE = 8f6d0151e4a9095c95925d6f6065214d382bf1dc
AF8_SOURCE_HEAD = 1922a5172f0e004dd95c279744c641775a80b15a
AF8_INTEGRATED = TRUE
AF8_RUN = 34222323657
AF8_EVIDENCE_STATUS = DIRECTLY_VERIFIED
B_SOURCE_HEAD = 2c6ceedebb250165893d942251acf7550346c405
B_SOURCE_TREE = e352588fad89977b4fbd98824e4b3872dc3bd41a
B1_RUN = 34266311850
B2_RUN = 34286249888
AUTHORIZED_B_PROMOTION_COUNT = 664
ACTUAL_B_PROMOTION_COUNT = 664
B1_DEFAULT_ZERO_HELD_UNKNOWN_COUNT = 6
COST_BLOCKERS_HELD_UNKNOWN_COUNT = 5
PRE_TOTAL = 4188
PRE_PASS = 285
PRE_UNKNOWN = 3903
POST_TOTAL = 4188
POST_PASS = 949
POST_UNKNOWN = 3239
B_UNKNOWN_BEFORE = 675
B_UNKNOWN_AFTER = 11
UNEXPECTED_STATUS_TRANSITIONS = 0
PROJECT_STATE_RECONCILED = TRUE
COVERAGE_PROMOTION = TRUE
FINAL_HEAD = terminal commit on this branch (code-freeze promotion commit c8d04e1064dfdd7fc068b03b2a170e19bc62cf7b; this handoff + PROJECT_STATE/operational-state are metadata-only on top)
FINAL_TREE = see push receipt (live tip verified before handoff delivery)
ARTIFACTS = WS33_INTEGRATED_CLOSURE_LEDGER.jsonl, WS33_INTEGRATED_WORK_QUEUE.json, WS33_INTEGRATED_FRONTIER_GATE.json, WS33_POST_AF8B_PROMOTION_EVIDENCE.json, WS33_CURRENT_OPERATIONAL_STATE.json, ws33_promote_b_frontier.py, WS33_ABC_B1_B2_PROMOTION_INDEX.json
ARTIFACT_DIGESTS = ledger 4db1d70b302390f72cd5265e8ade58ec48b92da36ae843e0a1395f0f202a6611; queue 02397404ebdc9d7a105466c3d24dc73c0f9844a8dbb55e626f4e0fb813202d3c; gate 9b1823378f2d3293a922eb7416f1fc2599019011279e54280f7871925c5086c9; promotion-evidence b53d535af2a5c2ae5f01ab972fd8b312df03a6dd4993c51b566816bbe03556e4; operational-state dbec07ddb4caf6f6625a6e23b03f0170bfae6f22873221ad14960a0739b8eeac; promote-script 3e6515b0b28147fb11dd93bb195575b8c9dc6b22e4006d55fc30fa0daba8f06e; promotion-index 98c4d143e9895430da226931f46b56eef25b044db2f1afb7b6b409342be7e1b5
PASS_EVIDENCE_INVALIDATED = FALSE
SOL_REVIEW_REQUIRED = TRUE
BLOCKERS = Sol High adjudication pending; 3239 UNKNOWN across A/B/C/D/E/F/G require future serial waves
NEXT_SERIAL_INTEGRATION_ACTION = Sol High adjudication; no further mutation without new PENDING freeze
