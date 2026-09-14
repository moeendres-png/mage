# WS214 Rules-RNG Call Accounting (post-fix)

- Unscripted coin: 8 draws -> getRulesRandomCalls == 8 (t3).
- Unscripted die: 8 draws -> == 8 (t4).
- Mixed 16+16 -> == 32 in-JVM (t5) and in every fresh-JVM probe
  (callsBefore=0, callsAfter=32; t9/t10).
- Twin games agree on counts as well as sequences.
- Scripted draws: 0 consumption (t1/t2) — adjudicated contract preserved.
- Queries (`getRulesSeed` / `isRulesSeedExplicit` / `getRulesRandom` /
  `getRulesRandomCalls`) consume nothing before or after draws (t8).
- Production delegate consumes identically (t7: harness calls == delegate calls).

RULES_RANDOM_CALL_ACCOUNTING = YES.
