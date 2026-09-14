# WS212 Consumption Accounting

`getRulesRandomCalls()` = number of `GameRandom.next(int)` gates since the last
seed. Diagnostics only, never authority.

Proven (DIRECTLY_VERIFIED):

- Resets to 0 on explicit reseed (`setRulesSeed`), before game start
  (`testReseedResetsStreamAndCounter`, `testExplicitSeedSetBeforeStartAcceptedAndQueriesFree`).
- Increments exactly with consumption: 60-card Fisher-Yates initial shuffle ==
  59 gates (`calls=59` in both fresh-JVM twins); single `nextBoolean` == 1 gate.
- Same-seed same-path twins carry equal counts at matching checkpoints
  (fresh-JVM digests; live-game digests t1/t2; consumer twins t4/t5/t6/t7 assert
  call-count equality explicitly).
- Queries consume nothing: `getRulesSeed`, `isRulesSeedExplicit`,
  `getRulesRandomCalls`, `getRulesRandom` leave the count unchanged (asserted).
- Failed fail-closed `init` consumes nothing (`calls == 0` after the throw).

`CONSUMPTION_ACCOUNTING = SEALED`.
