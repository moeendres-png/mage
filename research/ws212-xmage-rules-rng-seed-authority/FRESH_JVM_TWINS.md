# WS212 Fresh-JVM Twins (hard gate evidence)

Method: `mage.WS212FreshJvmProbe` launched via `ProcessBuilder` (separate OS
processes, separate JVMs) from `WS212RulesSeedAuthorityTest`
(`testFreshJvmTwinsSameSeedIdentical`, `testDifferentSeedControlDiverges`).

Probe path (exact production calls): `Deck.getMaindeckCards` →
`Library.addAll` (the `useDeck` path) → `Library.shuffle(game.getRulesRandom())`
(the body of `PlayerImpl.shuffleLibrary`) on a real `FakeGame` after
`setRulesSeed(seed)` + `setRequireExplicitSeed(true)`. Digest binds pre-start
order + seed + post-shuffle order + opening hand (top 7) + consumption count;
UUID-agnostic (names only).

## Same-seed twins (SEED_A = 0x5EED212A)

```
WS212-TWIN-A1 WS212-PROBE seed=1592598826 explicit=true pre=Plains,...,Forest post=... hand=... calls=59
WS212-TWIN-A2 WS212-PROBE seed=1592598826 explicit=true pre=... (identical)
```

- `FRESH_JVM_SAME_SEED_LIBRARY_EQUALITY = YES` (exact digest equality asserted).
- `FRESH_JVM_SAME_SEED_OPENING_HAND_EQUALITY = YES` (hand field identical).
- `RULES_RANDOM_CALL_COUNT_EQUALITY = YES` (`calls=59` both; 60-card Fisher-Yates).
- `INITIAL_SHUFFLE_SEEDED = YES`.

## Different-seed control (SEED_B = 0xBEEF212B)

- Same `pre=` across processes (input binding), different `post=`/`hand=`.
- `DIFFERENT_SEED_CONTROL = YES` (seed demonstrably controls the stream).

## Live-game twins (same JVM, full production path incl. init/events/turn flow)

`WS212SeededRulesConsumersTest` t1/t2: identical digest (turn, active player,
hands, ordered libraries, graves, battlefield, seed, explicit, calls).
t3 control diverges. t4/t5/t6/t7 extend equality to post-start consumers.

Evidence class: DIRECTLY_VERIFIED (fresh native processes for the shuffle core;
same-JVM live games for the full ceremony).
