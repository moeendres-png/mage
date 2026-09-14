# WS212 — Architecture Adjudication (XHIGH, read-first)

Source lock: `2b3f0f767b69192f90a921a9ece40abb0b8149d0`
(tree `38a1bcada4d694959fce68bcd4908fa07e7702c9`, exact WS211 terminal).
Adjudicated files (fresh inspection, this HEAD):

- `Mage/src/main/java/mage/game/Game.java` (Rules-RNG authority surface, ~L293-333)
- `Mage/src/main/java/mage/game/GameImpl.java` (ctor L183-204, copy L206-281,
  accessors L288-323, `init` gate L1311-1317 + shuffle L1381-1385,
  `pickChoosingPlayer` L1632-1645, `start` L1140-1147, `addPlayer` L453-457)
- `Mage/src/main/java/mage/util/GameRandom.java` (sole `next(int)` gate, counter, `copy()`)
- `Mage/src/main/java/mage/util/RandomUtil.java` (declared NON-RULES stream)
- `Mage/src/main/java/mage/players/PlayerImpl.java`
  (`useDeck` L415-422, `shuffleLibrary` L1937-1945, `discard` L850-919,
  `seekCard` L3041-3054, `flipCoinResult` L3194-3196, `rollDieResult` L3225-3227,
  bottom/top-of-library L1055-1061/L1198-1204)
- `Mage/src/main/java/mage/players/Library.java` (`shuffle(Random)` L39-49,
  deprecated no-arg `shuffle()` L57-60)
- `Mage/src/main/java/mage/game/GameState.java` (`Players` insertion order,
  `getPlayerList` L740-749)
- `Mage/src/main/java/mage/players/Players.java` (`extends LinkedHashMap`)
- `Mage/src/main/java/mage/cards/CardsImpl.java` (`getRandom` L80-96)
- `Mage/src/main/java/mage/target/TargetImpl.java` (random pick L468-498)
- `Mage/src/main/java/mage/cards/decks/Deck.java` (`getMaindeckCards` L212-221)
- `Mage/src/main/java/mage/game/mulligan/{London,SmoothedLondon}Mulligan.java`
- `Mage.Server.Plugins/.../CommanderFreeForAll.java` (delegating ctor, no RNG)
- `Mage/src/main/java/mage/game/FakeGame.java` (test game, no RNG of its own)

## Answers

1. **GameRandom first constructed — `GameImpl` constructor** (L197-199), from a
   UUID-derived default seed
   (`UUID.randomUUID()` MSBs ^ LSBs). Copy constructor (L256-257) duplicates via
   `GameRandom.copy()`, never shares. Defensive lazy rebuild in `getRulesRandom()`
   (L290-296) only fires if a subclass bypassed the constructors.

2. **`setRulesSeed` is safely invocable at any point after construction**, and MUST
   land before `start`/`init` for credited runs. It fully replaces the stream
   (`new GameRandom(seed)`), so call order construction → `setRulesSeed` →
   `start`/`init` is a clean binding window.

3. **No Rules-random value is consumed before callers can invoke `setRulesSeed`.**
   The constructor performs zero `getRulesRandom()` consumption. The
   construction→seed window operations — `addPlayer` → `useDeck` → `Library.addAll`
   (insertion, no RNG), `state.addPlayer` (map insert), `initPlayerDefaultWatchers`
   (no RNG), `Deck.getMaindeckCards` (order-preserving collect, no RNG) — consume
   nothing. First consumption is inside `init` (initial shuffle, L1381-1385).

4. **`GameImpl.init` enforces `requireExplicitSeed` FIRST** (L1314-1317,
   `IllegalStateException`), before companion handling, before initial shuffle
   (L1381-1385), before choosing-player pick (L1398+), before `drawHand`/mulligan
   (L1442/1447), before coin/die/opening-hand/planechase consumption. Fail-closed
   before any Rules-random consumption: YES.

5. **`setRulesSeed` resets all three**: new `GameRandom(seed)` resets stream state
   AND the consumption counter to 0 (via `GameRandom.setSeed`), and sets
   `rulesSeedExplicit = true`. Directly covered by
   `WS54RulesRngTest.testGame_RulesSeedAuthority`.

6. **Post-construction, pre-`start`/`init` `setRulesSeed` is SUFFICIENT for complete
   deterministic initial shuffle.** Pre-shuffle order is deterministic
   (`LinkedHashSet` materialization + `LinkedHashMap` player insertion order), the
   shuffle call is `library.shuffle(game.getRulesRandom())`, and nothing consumes
   the stream in between.

7. **Constructor-level seed API is NOT necessary.** No consumption exists in the
   binding window, so a constructor parameter buys no additional determinism.

8. **No race or pre-start consumption exists that `setRulesSeed` cannot cover.**
   Construction, seeding, and `start` are orchestrated synchronously on one thread;
   no background thread touches `getRulesRandom()` before `init`.

9. **The default UUID-derived seed serves an intentional non-credited purpose**:
   every game carries a recorded replay identity (`getRulesSeed()`), while ordinary
   games stay nondeterministic (`isRulesSeedExplicit() == false`). This distinction
   is load-bearing for the hard gates (no constant default seed; defaults need not
   reproduce across runs). PRESERVE.

10. **Replacing default UUID seeding with `RandomUtil` would violate the project's
    explicit Rules-vs-non-Rules separation** (declared in `RandomUtil`'s own
    javadoc and the WS212 hard gates). It would couple the Rules stream's identity
    to the shared non-Rules stream. FORBIDDEN; not implemented.

11. **No production Rules-random consumer bypasses `getRulesRandom()` in scope.**
    Re-verified at this HEAD: `RandomUtil.next*` in `Mage/src/main` +
    `Mage.Sets` = allow-listed non-Rules sites only (booster collation, AI-only
    `setRandomChoice`, cosmetic repositories, sealed/draft/tournament infra,
    `MagesContest` AI bid guard); every `Collections.shuffle` in card/engine code
    takes `game.getRulesRandom()` (the two no-arg shuffles are draft/swiss infra);
    all 1-arg `randomFromCollection` callers are AI/cosmetic. Matches the WS54
    closure (`unknown_in_scope: 0`).

12. **Representative `getRulesRandom` consumers were audited for iteration order**:
    `Deck.getMaindeckCards` (LinkedHashSet declared order), `Players`
    (LinkedHashMap insertion/table order → `pickChoosingPlayer` array and
    `getPlayerList` deterministic), `CardsImpl.getRandom` (LinkedHashSet),
    `TargetImpl` random pick (flow-ordered `randomPossibleTargets`), battlefield
    (LinkedHashMap insertion order per closure), `seekCard`/`getRandomToDiscard`
    (flow order), scalar coin/die/choosing-player (order-free). No proven residual
    Rules-relevant iteration nondeterminism at this HEAD; WS212 fresh-JVM twins
    are the runtime check, not normalization.

13. **Copy/simulation preserves correctly**: copy ctor duplicates RNG state via
    `GameRandom.copy()` (child starts at parent's current position, independent
    object). `getRulesSeed`/`rulesSeedExplicit`/`requireExplicitSeed` propagate.
    Covered by `WS54RulesRngTest.testGame_RulesSeedAuthority` +
    `testCopy_DuplicationIsolatesParent`.

14. **Sibling AI simulations cannot perturb the parent stream** (duplicate-never-share;
    sim RNG never written back). Two siblings from identical parent state
    intentionally start at identical RNG positions — documented AI-search heuristic
    limitation, attested in code (GameImpl L252-255) and closure. DESIRABLE/KNOWN.

15. **Minimal truthful core contract** (Lab/provider burden):
    (a) each `Game` owns exactly one `GameRandom`, never shared, never global;
    (b) construction records a nondeterministic default seed, explicit flag false;
    (c) credited orchestration calls `setRulesSeed(seed)` after construction and
    before `start`/`init` (resets stream + counter + explicit flag);
    (d) credited harnesses additionally set `setRequireExplicitSeed(true)` so `init`
    fails closed before any Rules consumption when the seed is absent;
    (e) every Rules-random selection consumes only `game.getRulesRandom()` over
    flow-ordered candidates; (f) `RandomUtil` (incl. `setSeed`) is never Rules
    authority; (g) copies duplicate-never-share; siblings may coincide by design;
    (h) `getRulesRandomCalls()`/seed getters are diagnostics and consume nothing.

## Classification

**EXISTING_CORE_API_SUFFICIENT_NEEDS_TEST_HARDENING**

No production mutation is justified: the existing
`setRulesSeed` + `requireExplicitSeed` API already forms the complete correct
engine contract, and every adjudicated binding point is already game-scoped.
WS212 therefore adds engine-side qualification (fresh-JVM twins, consumer
representatives, accounting, copy isolation, WS206/WS211 regressions) and the
consolidated Lab successor spec — zero production diff, zero behavior-credit
change.

Evidence class: CODE_DERIVED (call-chain audit above) + DIRECTLY_VERIFIED
(WS212/WS54 runtime corpus, see VALIDATION.md).
