# WS212 Validation

## Test matrix (all DIRECTLY_VERIFIED, reactor-fresh artifacts)

| # | Criterion | Evidence | Result |
|---|---|---|---|
| 1 | Explicit required + absent → fail before consumption | `WS212RulesSeedAuthorityTest.testRequireExplicitSeedAbsentFailsClosedBeforeConsumption` (calls==0 after throw) | PASS |
| 2 | Explicit set before start → accepted | `...testExplicitSeedSetBeforeStartAcceptedAndQueriesFree` | PASS |
| 3 | Fresh-JVM twin initial shuffle | `...testFreshJvmTwinsSameSeedIdentical` (2 processes, exact digest equality) | PASS |
| 4 | Fresh-JVM twin opening hand | same (hand field identical) | PASS |
| 5 | Same-path `rulesRandomCalls` equality | fresh-JVM `calls=59` + live digests + t4/t5/t6/t7 count asserts | PASS |
| 6 | Distinct-seed control | engine probe + live t3 + coin/die control | PASS |
| 7 | Reseed resets stream/counter pre-start | `...testReseedResetsStreamAndCounter` | PASS |
| 8 | Default recorded, explicit false | `...testDefaultSeedRecordedButNotExplicit` | PASS |
| 9 | In-game shuffle reproducibility | `WS212SeededRulesConsumersTest.t4` (production `shuffleLibrary`) | PASS |
| 10 | Coin/die representatives | `...t5` via production `computerPlayer` delegate | PASS |
| 11 | Random discard/target representatives | `...t6` (discardOne→CardsImpl.getRandom); TargetImpl shared gate audited + same-gate runtime | PASS |
| 12 | Simulation copy isolates parent | engine test + live `t8` | PASS |
| 13 | WS206 narrow regression | 13/13 | PASS |
| 14 | WS211 narrow regression | 20/20 | PASS |
| — | WS54 Mage corpus (no drift) | 13/13 | PASS |
| — | WS54 game gates (no drift) | 7/7 | PASS |

Mulligan: London reshuffle consumes only via qualified `shuffleLibrary`
(CODE_DERIVED); Smoothed-London `drawHand` runtime-proven (t7).

## Commands (offline, `-o`)

- `mvn -pl Mage test -Dtest='WS212RulesSeedAuthorityTest' ...` → 8/8.
- `mvn -pl Mage test -Dtest='WS54RulesRngTest' ...` → 13/13.
- `mvn -pl Mage.Tests -am test -Dtest='WS212SeededRulesConsumersTest' ...` → 8/8.
- `mvn -pl Mage.Tests -am test -Dtest='WS54SeededReexecutionTest,...WS206...,WS211...' ...` → 15/15 and 33/33.

(`-am` required: without it Maven resolves a stale installed `mage` jar;
with `-am` all green. See WS206_REGRESSION.md.)

## Classification

- `CORE_PRODUCTION_CHANGE = NONE` (`NO_NEW_CORE_PRODUCTION_CHANGE_REQUIRED`).
- `GLOBAL_BEHAVIOR_CREDIT_CHANGE = 0`, `FULL107 = NOT_RUN`,
  `D5_TWIN_EQUALITY = UNKNOWN` (Lab-side; WS213 burden).
- `ARCHITECTURE_FREEZE = NOT_CLAIMED`, `PRODUCTION_PROVIDER = NOT_SELECTED`,
  `RAW_GIT_PUSH_USED = NO`.
