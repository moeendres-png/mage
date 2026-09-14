# WS214 WS212 Regression (smallest directly relevant set)

Preserved (all post-fix, unmodified WS212 tests):
- Mage module `WS212RulesSeedAuthorityTest`: 8/8 PASS (explicit-seed contract,
  fresh-JVM twins, different-seed control, reseed, default seed, non-Rules
  storm isolation, copy isolation).
- Mage module `WS54RulesRngTest`: 13/13 PASS (Rules-RNG core).
- Mage.Tests `WS212SeededRulesConsumersTest`: 8/8 PASS — explicit seed
  contract, fresh-JVM-equivalent rerun equality, other-seed divergence,
  in-game shuffle, coin/die via production delegate (t5), random discard,
  smoothed-mulligan draw, live-copy isolation.
- Scripted live-game suites (scripted-precedence compatibility):
  `FlipCoinTest` 3/3 PASS, `RollDiceTest` 29/29 PASS.

WS212 production conclusions unchanged; no production file touched.
WS212_REGRESSION = PASS (21 engine + 8 consumers + 32 scripted card tests).
