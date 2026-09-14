# WS214 Pre-Fix Reproducer (runtime, fresh JVMs)

Run: `mvn -pl Mage.Tests -Dtest=WS214TestPlayerRulesRngTest ... test` on the
UNMODIFIED tree (10 tests, 6 failed as designed; scripted/query tests passed).
Full failure log in session record; key bound facts below.

Fresh-JVM twins, same explicit seed 1592598858 (two separate `java` processes,
pids 752114 / 752137, `WS214FreshJvmProbe`: fresh FakeGame + setRulesSeed +
TestPlayer, 16 unscripted coins + 16 unscripted d6):

- TWIN-A1: coins=H,H,T,H,T,T,T,H,H,T,H,H,H,T,T,H
  dice=d4,d3,d4,d3,d4,d5,d2,d1,d6,d1,d2,d4,d4,d4,d3,d5
  callsBefore=0 callsAfter=0
- TWIN-A2: coins=H,T,T,T,H,T,H,H,H,H,H,H,T,H,T,H
  dice=d5,d1,d2,d2,d4,d4,d4,d6,d5,d5,d6,d5,d5,d1,d1,d3
  callsBefore=0 callsAfter=0
- Both twins: ctrlCoins=T,H,T,T,H,T,H,T,T,H,T,H,H,T,T,T (IDENTICAL),
  ctrlDice=d1,d6,d1,d2,d4,d2,d2,d1,d3,d3,d3,d2,d3,d6,d5,d1 (IDENTICAL).

Binding:
- rules seed: 1592598858 explicit=true in both processes.
- rulesRandomCalls before/after: 0 -> 0 in both (32 unscripted draws consumed
  ZERO Rules gates).
- TestPlayer result: DIFFERS across the two JVMs (same seed, same path).
- RandomUtil involvement: proven — consumption outside the game stream
  (callsAfter=0) plus divergence while the direct Rules-control stream
  (GameRandom(seed)) is byte-identical across the processes.
- process identity: pids above, diagnostic metadata only.

In-JVM defect signatures (same run):
- t3/t4/t5: "expected:<8> but was:<0>" / "expected:<32> but was:<0>".
- t7 production parity: harness draws != production-delegate draws on
  same-seed games.
- t1/t2 (scripted precedence), t6 (different-seed control), t8 (queries free):
  PASS pre-fix — established contracts, preserved post-fix.

Conclusion: exact WS212 harness problem reproduced at runtime, not inferred
from source. FLIP_COIN_UNSCRIPTED_RULES_RNG (pre-fix) = NO;
ROLL_DIE_UNSCRIPTED_RULES_RNG (pre-fix) = NO.
