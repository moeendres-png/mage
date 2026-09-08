# WS33 serial integration (AF8 -> B) — Phase IV PENDING checkpoint (pre-mutation freeze)

Date: 2026-09-09. Status: PENDING. `COVERAGE_PROMOTION=FALSE`.
No canonical coverage or identity registry has been modified. The next mutation
may promote EXACTLY the 664 authorized paths below and nothing else.

## Frozen integration source

- Integration HEAD at PENDING: `9295d63ad1...` (parent chain contains AF8_SOURCE_HEAD `1922a5172f0e004dd95c279744c641775a80b15a`; canonical base `6da237b704ba5e66c58c2334f47e36ef68ca980d`).
- AF8 inherited: source HEAD/TREE `1922a51...`/`ef71c0d0...`; run `34222323657` SUCCESS; artifact `10054400356` digest `sha256:026df6dd6f770fe8f93c5efc96c17b2d473876a5b01f44d9ccbc24df96ae727c`; gate 8 paths / 0 failures / coverage unmutated.
- B source HEAD/TREE: `2c6ceedebb250165893d942251acf7550346c405` / `e352588fad89977b4fbd98824e4b3872dc3bd41a`.
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- Model digests: manifest `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`, consumer `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`.
- B1: run `34266311850`, job `102196461658`, artifact `10072131808` digest `sha256:118de4169ae9abf4ab500213430a62cd67630d44cb9b34ce3032a93907a29c2f`, source `80bc5fa2b2f99d2b763ab09d4194370ba631ca91`, gate PASS (273 records: 267 EXTERNALLY_RULE_VALIDATED + 6 TECHNICALLY_CONFORMANT defaults).
- B2: run `34286249888`, job `102262427048`, artifact `10079683394` digest `sha256:a8a498f63a776a772a78d531b21ffc1542c59bb218f10185f135271078aa00b3`, source `c0b8c57e7e29b7620ddf27ec768f29d1619460b7`, gate PASS (397 EXTERNALLY_RULE_VALIDATED).
- B1 273 target-list digest reproduced: `30dd81f733e0c1dfdb2d3020c0b9b1e0a2ed542fcf78123d641839fb24800024`.

## Authorized 664-path set (recomputed from immutable artifacts, not trusted from proposal)

- Digest: `sha256:57e210b8d2a5a79f3aaa3a4b124e3d92e2d6d3fc8447fa74d31f299d9366f75c` (sorted IDs, LF-joined, trailing newline).
- Composition: 267 B1 `forge.game.ability.AbilityUtils#calculateAmount` + 397 B2 `forge.game.cost.Cost`; all `logical_bucket=WS33B`; all evidence class EXTERNALLY_RULE_VALIDATED.
- B1 positives and B2 positives are pairwise disjoint (overlap 0); full B1 273 and B2 397 are pairwise disjoint (overlap 0).

## Held sets (remain UNKNOWN; excluded from promotion)

- Six B1 default-zero paths (TECHNICALLY_CONFORMANT + `default_zero_evidence`, Sol High: REMAIN UNKNOWN):
  `3cf0e40156206f9105726b552a1e0f3bde510084` (Estinien Varlineau),
  `50b392b0cd4bd8e5986cf93bb10a06539625d070` (Estinien Varlineau),
  `7a831f5f073c8838d1d99c2bf9a7c464848738df` (Kemba's Legion),
  `861f002e827babcf7c74379618b58370bcd3b24c` (Exsanguinate),
  `91cf40efbb4fb380b8f786fb0db85e2153d119d2` (Hoarder's Greed),
  `b18cf934f97ef360910595dfd19b1f57ca608df7` (Inferno Trap).
  Card mapping corroborated via ledger source provenance against
  `WS33B_B1_DEFAULT_ZERO_ADJUDICATION_20260908.md`.
- Five Cost terminal blockers (TERMINAL_IN_PIN, remain UNKNOWN):
  `83da92d042e1c29d770df07397319afb1a2acb9d` (Conspiracy Theorist),
  `8671678f79ce684700bee73e1fedcbdd2cc4fa94` (Greenwarden of Murasa),
  `f4c7f4744d2aafd7867c487427756616567b0177` (Cavalier of Thorns),
  `e45204fac7594e256cef247c35ef92defba2b797` (Foot Chopper),
  `fdfdd242632a5ba2208e4acace7b4500bb347efe` (Blazing Torch).

## Live pre-promotion totals (recomputed from integration worktree)

- Branch ledger: TOTAL=4188 PASS=285 UNKNOWN=3903 FAIL=0 UNSUPPORTED=0.
- UNKNOWN by shard: A=179 B=675 C=700 D=920 E=1029 F=319 G=81 H=0.
- Branch queue: unresolved=3903, work items=236.
- Operational successor truth (artifact `9979204198`, immutable): PASS=488 UNKNOWN=3700, B_UNKNOWN=675. Branch files at 285/3903 are superseded coordination files; promotion base below is the live branch ledger, with the operational layer reconciled in Phase VI.

## Disjointness results (all recomputed; any nonzero overlap would be a hard gate failure)

- authorized-664 vs branch PASS (285): overlap 0.
- authorized-664 vs operational PASS (488, incl. 203 G3/A1 the proposal did not check): overlap 0.
- authorized-664 vs six held defaults: overlap 0. authorized-664 vs five blockers: overlap 0. defaults vs blockers: overlap 0.
- All 664 are UNKNOWN in BOTH the branch ledger and the successor-artifact ledger.
- All 6 defaults and all 5 blockers are UNKNOWN in BOTH ledgers.
- Queue binding: branch B1 queue item (template-010) == B1 full 273 exactly; branch Cost queue union (090/186 + 091/8 + 092/206 + 093/2) == B2 397 + 5 blockers exactly.

## Expected transition

Exactly 664 UNKNOWN->PASS (267 B1 + 397 B2) with retained EXTERNALLY_RULE_VALIDATED classification.
Expected post state (branch layer): PASS=949 UNKNOWN=3239, B_UNKNOWN=11 (6 defaults + 5 blockers), all other shards unchanged, zero unexpected transitions.
Sol High decisions enforced: six defaults stay UNKNOWN; five Cost blockers stay UNKNOWN.

## Classification

All identities/counts/sets: DIRECTLY_VERIFIED by recomputation against immutable artifacts and live files.

`COVERAGE_PROMOTION=FALSE`. `WS33_COMPLETE=FALSE`. `TASK_COMPLETE=NO`.
