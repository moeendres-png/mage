# WS214 Fresh-JVM Validation (post-fix, separate processes)

Suite: `WS214TestPlayerRulesRngTest` t9/t10; probe `WS214FreshJvmProbe`
(FakeGame + explicit seed + 16 unscripted coins + 16 unscripted d6 +
direct-Rules control draws). 10/10 tests PASS post-fix.

1. Same seed + unscripted coin, same result sequence: YES.
   TWIN-A1 (pid 755002) == TWIN-A2 (pid 755030), seed 1592598858:
   coins=T,H,T,T,H,T,H,T,T,H,T,H,H,T,T,T.
2. Same seed + unscripted die, same result sequence: YES.
   dice=d1,d6,d1,d2,d4,d2,d2,d1,d3,d3,d3,d2,d3,d6,d5,d1 in both twins.
3. Same seed + mixed coin/die, same semantic sequence: YES (coins+dice above).
4. Matching Rules-RNG call counts: YES — callsBefore=0, callsAfter=32
   in every probe process; in-JVM twins agree (t5).
5. Harness == Rules-control sequence in-process: YES —
   coins==ctrlCoins and dice==ctrlDice (same seed, same algorithm, same order).

Semantic output + authoritative stream accounting compared; no bit-exact
process-identity claim (pids differ by design).
FRESH_JVM_SAME_SEED_COIN_EQUALITY = YES.
FRESH_JVM_SAME_SEED_DIE_EQUALITY = YES.
FRESH_JVM_MIXED_SEQUENCE_EQUALITY = YES.
