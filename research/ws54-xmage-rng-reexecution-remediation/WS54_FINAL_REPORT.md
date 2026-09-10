# WS54 Final Report — XMage Controlled Rules RNG + Reexecution Remediation

## Verdict

`XMAGE_RNG_REEXECUTION_REMEDIATION_PASS`

Pre-repair M5 reproduced (R1-R5) at the source lock; systemic per-game Rules RNG
authority implemented; setup-order determinism established; all production Rules
random sites in the claimed Commander scope routed to the game-scoped (or
match-scoped) RNG with zero UNKNOWN remaining; cross-game isolation, non-Rules
perturbation isolation, same-seed semantic reexecution, and fresh-process
reexecution all PASS at unit and full-game levels; all 7 negative detector controls
demonstrated; no existing test modified; nearest-module + affected-path regressions
green.

## What was wrong (WS52 M5 confirmed, not reclassified)

1. `Deck.getMaindeckCards()` destroyed declared deck order via `Collectors.toSet()`.
2. One static JVM-global `Random` served every game, AI search, and Rules path.
3. `Library.shuffle()` + 2× `PlayerImpl` + 5× card-file shuffles took no RNG argument.
4. `CardsImpl.getRandom` / `seekCard` picked from HashSet-scrambled candidates.
5. Snapshot/rollback state never bound RNG.

## What was built

- `mage.util.GameRandom` (final, extends `Random`, same LCG statistics, synchronized
  sole entropy gate, explicit seed, exact-state `copy()`, call counter, serializable).
- `Game` authority (`getRulesRandom/setRulesSeed/getRulesSeed/isRulesSeedExplicit/
  getRulesRandomCalls/setRequireExplicitSeed`); `GameImpl` ownership + copy
  duplication + credited fail-closed `init`; `pickChoosingPlayer` game-scoped.
- `Library.shuffle(Random)` (production Fisher-Yates, explicit RNG); deprecated
  no-arg fallback retained for AI/test only with a production-zero gate.
- Setup/canonical order: `LinkedHashSet`/`LinkedHashMap` preservation at every
  Rules-random input (deck, library candidates, all `possibleTargets` impls,
  attack watcher, counters, Camouflage map, ChaosDefiler set, Ziatora land set,
  ExposeTheCulprit move input, unique-cards views). No identity/UUID-hash sorting.
- Full call-site migration: core effects, Modes, TargetImpl random branch,
  SmoothedLondonMulligan (threaded `GameRandom`), Match seating (match-scoped RNG +
  explicit seed), Plane/Momir/Dungeon, 51 Mage.Sets card files, MCTS:282 AI consumer
  to the non-Rules stream. `TargetOptimization` prune stays non-Rules per
  adjudication; `ChoiceImpl.setRandomChoice` stays non-Rules (AI-only callers).
- `RandomUtil` re-designated, behavior-identical, as the NON-RULES stream.

## Evidence map (all under `research/ws54-xmage-rng-reexecution-remediation/`)

- `WS54_SOURCE_LOCK.md`, `WS54_PRE_REPAIR_M5_REPRO.json`
- `WS54_RANDOMNESS_INVENTORY.json/.md` (16 RULES + 4 SETUP + AI/UI/INFRA/TEST/
  IDENTITY groups, UNKNOWN 0)
- `WS54_RNG_ARCHITECTURE.md`, `WS54_SETUP_ORDER_ANALYSIS.md`
- `WS54_RULES_RNG_CALLSITE_CLOSURE.json` (per-site attestation + grep gates)
- `WS54_GAME_ISOLATION.json`, `WS54_NONRULES_PERTURBATION.json`
- `WS54_FRESH_PROCESS_REEXECUTION.json` (unit digest + 2675-char game digest,
  byte-identical across separate JVMs)
- `WS54_NEGATIVE_CONTROLS.json` (7/7 detectors fire)
- `WS54_SNAPSHOT_REPLAY_DISPOSITION.md` (arbitrary restore NOT_QUALIFIED)
- `WS54_HISTORICAL_IMPACT_LEDGER.json` (5× TARGETED_REQUALIFICATION_REQUIRED,
  M5 INVALIDATED/superseded)
- `WORKSTREAM_STATE.yaml` (terminal PASS)

## Tests (exact commands, all BUILD SUCCESS)

- `mvn -pl Mage test` → 112/112 (incl. new `WS54RulesRngTest` 13/13: P1 setup+shuffle,
  P2, P3, P4, copy isolation, seed authority, fail-closed init, 4 unit negatives, P5 digest)
- `mvn -pl Mage.Tests test -Dtest=WS54SeededReexecutionTest` → 7/7 (P1-game/P6,
  same-JVM rerun, P2-game, P3-game, P4-game, decision + progression negatives)
- Fresh-process: `mvn -pl Mage.Tests surefire:test
  -Dtest='WS54SeededReexecutionTest#t1_captureSeedA'` × 2 JVMs → identical digests;
  same for unit P5 digest.
- Regressions: mulligan pkg + FlipCoin + RollDice + GripOfChaos (70 reports, 0 fail);
  commander slice 23 classes/69 tests 0 fail; RandomTest green.
- Existing tests modified: ZERO.

## Inventory totals

RULES_RNG 16, SETUP_RULES_RNG 4, AI_RNG 3, UI_RNG 1, INFRASTRUCTURE_RNG 5,
TEST_RNG 1, IDENTITY_ONLY_RANDOMNESS 1, UNKNOWN 0.

## Historical impact totals

NO_IMPACT 0, TARGETED_REQUALIFICATION_REQUIRED 5, INVALIDATED 1, UNKNOWN 0.

## Residual risks (honest)

1. Inventory completeness for future edits: the production-zero gate (test + grep
   closure) must be re-run by any follow-up touching randomness; a new Rules caller
   on the global stream would silently reintroduce nondeterminism (only P-corpus
   reexecution catches it).
2. MomirEmblem candidate order depends on repository row order (Momir-only, outside
   Commander scope).
3. Event-log ordering from non-RNG identity-hash iteration (e.g., zone-move input
   sets) was fixed only where encountered (ExposeTheCulprit); whole-engine
   event-log canonicalization was out of scope — semantic digests compare multiset/
   flow-ordered state, not log order.
4. Sibling AI sims start at identical RNG positions (documented search limitation).

## Project state (unchanged, repeated)

`BEHAVIOR_CREDIT = 0/107` · `FULL107 = NOT_RUN` ·
`ARCHITECTURE_FREEZE = NOT CLAIMED` · `PRODUCTION_PROVIDER = NOT SELECTED`
