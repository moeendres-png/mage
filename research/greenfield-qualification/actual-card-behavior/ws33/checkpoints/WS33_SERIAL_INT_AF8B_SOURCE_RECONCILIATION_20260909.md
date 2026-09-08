# WS33 serial integration (AF8 -> B) — Phase I source reconciliation

Date: 2026-09-09. Branch: `work/ws33-serial-integration-af8-b-20260909` (dedicated worktree, isolated from shared mutable worktree).
Status: SOURCE_LOCK_VERIFIED. No integration writes performed yet. `COVERAGE_PROMOTION=FALSE`.

## Source locks (all re-read live 2026-09-09, no defect)

- CANONICAL_BASE_HEAD = `6da237b704ba5e66c58c2334f47e36ef68ca980d`
- CANONICAL_BASE_TREE = `8f6d0151e4a9095c95925d6f6065214d382bf1dc`
- `origin/work/ws33-g3-final-closure-20260902` HEAD == CANONICAL_BASE_HEAD (unmoved).
- AF8_SOURCE_HEAD = `1922a5172f0e004dd95c279744c641775a80b15a`
- AF8_SOURCE_TREE = `ef71c0d06398dd4ae760ccf5cef69264b1b02fa6`
- `origin/work/ws33-af8-evidence-contract-repair-20260908` HEAD == AF8_SOURCE_HEAD (unmoved).
- AF8 ancestry: `git merge-base --is-ancestor` TRUE; AF8 is exactly 6 commits ahead, 0 behind canonical base (direct descendant; fast-forward-equivalent integration required).
- WS33B_SOURCE_HEAD = `2c6ceedebb250165893d942251acf7550346c405`
- WS33B_SOURCE_TREE = `e352588fad89977b4fbd98824e4b3872dc3bd41a`
- `origin/work/ws33-b-high-throughput-20260907` HEAD == WS33B_SOURCE_HEAD (unmoved).
- Integration branch created from exactly CANONICAL_BASE_HEAD; verified HEAD/TREE equal the canonical locks above.
- FORGE_PIN = `8c7e9afb8e6caee88644b94e25da5852e36f8928` (canonical PROJECT_STATE, operational state, B1/B2 gates all agree).
- MODEL_MANIFEST_DIGEST = `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- MODEL_CONSUMER_DIGEST = `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`
- WS33B_TARGET_DIGEST (B1 273-path target list) resolved from repository evidence and reproduced by recomputation: `30dd81f733e0c1dfdb2d3020c0b9b1e0a2ed542fcf78123d641839fb24800024`.

No SOURCE_LOCK_DEFECT. No source branch was modified; C (`ada567e664e679dccb84dea07fb00de198880ba6`) untouched and out of scope.

## Live GitHub run/artifact verification (DIRECTLY_VERIFIED via gh API 2026-09-09)

- AF8 run `34222323657` (`WS33 ABC A-rest SVar AF8 runtime`): completed SUCCESS at exactly AF8_SOURCE_HEAD on the AF8 branch. Artifact `10054400356` (`ws33-abc-a-rest-svar-af8-34222323657`), digest `sha256:026df6dd6f770fe8f93c5efc96c17b2d473876a5b01f44d9ccbc24df96ae727c`.
- B1 run `34266311850`, job `102196461658`: completed SUCCESS at `80bc5fa2b2f99d2b763ab09d4194370ba631ca91`. Artifact `10072131808`, digest `sha256:118de4169ae9abf4ab500213430a62cd67630d44cb9b34ce3032a93907a29c2f` (matches B proposal and B1 PASS checkpoint).
- B2 run `34286249888`, job `102262427048`: completed SUCCESS at `c0b8c57e7e29b7620ddf27ec768f29d1619460b7`. Artifact `10079683394`, digest `sha256:a8a498f63a776a772a78d531b21ffc1542c59bb218f10185f135271078aa00b3` (matches B proposal and B2 PASS checkpoint).
- Successor artifact `9979204198` (run `34000014860`), digest `sha256:ae75ff01604f9fcc2b2cd2320e4cec1470347bcd47665d1989c1541542e76af0` (matches PASS checkpoint).

## Live pre-promotion coverage state (recomputed, not trusted from caches)

Branch-level `WS33_INTEGRATED_CLOSURE_LEDGER.jsonl`: 4188 records, PASS=285, UNKNOWN=3903, FAIL=0, UNSUPPORTED=0.
UNKNOWN by shard: WS33A=179, WS33B=675, WS33C=700, WS33D=920, WS33E=1029, WS33F=319, WS33G=81, WS33H=0.
Branch work queue: unresolved=3903, work items=236.

## Known stale metadata (recorded, not treated as authority)

1. Canonical `PROJECT_STATE.md` / `WS33_CURRENT_OPERATIONAL_STATE.json` claim PASS=488 / UNKNOWN=3700 with A_UNKNOWN=57, G_UNKNOWN=0. Those counts are operationally true only via immutable successor artifact `9979204198` (488 PASS verified inside the downloaded artifact: branch 285 + 203 G3/A1). The branch-level ledger/queue/frontier-gate coordination files remain at 285/3903 and are explicitly superseded for operational frontier purposes by that artifact (`POST_G3_A1_SUCCESSOR_RUN_34000014860_PASS.md`). This integration recomputes from live files and reconciles explicitly in Phase VI.
2. The B proposal's cached successor math mixes bases (`285+664=949` vs `3700-664=3036`); this integration recomputes both layers live and does not trust cached totals.
3. The B proposal verified disjointness only against the 285 branch PASS set; this integration additionally verifies against the full 488 operational PASS set (Phase III).
4. Canonical `PROJECT_STATE.md` open-gate text describes superseded AF8 PENDING state (run `34164631499`); AF8 repair SUCCESS (run `34222323657`) supersedes it. Repaired in Phase VI.

## B promotion sets (extracted from immutable artifacts, recomputed 2026-09-09)

- B1: 273 records = 267 EXTERNALLY_RULE_VALIDATED positive + 6 TECHNICALLY_CONFORMANT `default_zero_evidence` (exact IDs in Phase III precheck; held UNKNOWN per Sol High decision).
- B2: 397 records, all EXTERNALLY_RULE_VALIDATED positive.
- Authorized promotion union: 664 paths, digest `sha256:57e210b8d2a5a79f3aaa3a4b124e3d92e2d6d3fc8447fa74d31f299d9366f75c` (sorted IDs, LF-joined with trailing newline).
- 5 Cost terminal blockers (exact IDs in `ws33_filter_abc_b2_cost_campaign.py` TERMINAL_BLOCKERS): held UNKNOWN.

## Classification

Source/ancestry/run/artifact/digest facts: DIRECTLY_VERIFIED. Live counts: DIRECTLY_VERIFIED by recomputation. No coverage mutation performed.

`COVERAGE_PROMOTION=FALSE`. `WS33_COMPLETE=FALSE`. `TASK_COMPLETE=NO`.
