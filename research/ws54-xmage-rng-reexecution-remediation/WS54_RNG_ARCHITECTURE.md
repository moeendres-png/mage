# WS54 RNG Architecture (as implemented)

Binding XHIGH adjudication: `foundry-adjudicator` ruling (D1-D10 + a-d, no
`AUTHORITY_GATE`), preserved in `WORKSTREAM_STATE.yaml` milestones. Deltas from the
proposal are all incorporated below.

## Authority

- New `Mage/src/main/java/mage/util/GameRandom.java`: `final class extends
  java.util.Random` (direct `Collections.shuffle(list, gameRandom)` use), same 48-bit
  LCG as `Random` (identical statistics; control change only), `synchronized` sole
  entropy gate `next(int bits)`, explicit `GameRandom(long seed)`, exact-state
  `copy()` (duplicates gaussian cache + call counter, consumes nothing),
  `getCallsCount()` diagnostics-only, `serialVersionUID` (Java 8 target).
- `Game` gains `getRulesRandom / setRulesSeed / getRulesSeed / isRulesSeedExplicit /
  getRulesRandomCalls / setRequireExplicitSeed`. `GameImpl` owns the instance; the
  copy constructor duplicates (never shares) state; `getRulesRandom()` never null.
- `RandomUtil` keeps the behavior-identical static stream, re-documented NON-RULES
  only (AI/UI/infra/test). `setSeed` is non-Rules/test use only. No ThreadLocal, no
  static game pointer, no global map.

## Initialization

- Default construction seeds from `UUID.randomUUID()` msb^lsb, recorded as
  `rulesSeed` with `rulesSeedExplicit=false` (labeled non-credited default).
- Credited orchestration calls `setRulesSeed(seed)` before `init` (resets stream +
  counter + flag). With `setRequireExplicitSeed(true)`, `init` fails closed on a
  missing explicit seed (proven by `testGame_CreditedInitFailsClosedWithoutExplicitSeed`).
- Pilot supplies the seed only; every Rules-random selection is performed by the engine.

## Isolation

- Per-game: separate `GameRandom` per `Game` object; interleaved consumption proven
  (`testP3_InterleavedGamesIsolated`).
- Non-Rules: AI (`ComputerPlayer`, MCTS, MAD, `ChoiceImpl.setRandomChoice`),
  UI, infra, tests stay on `RandomUtil`; proven non-perturbing
  (`testP4_NonRulesPerturbationIsolated`).
- AI-sim copies (`createSimulationForAI/ForPlayableCalc` via `Game.copy`) duplicate
  RNG state: zero parent perturbation (proven by `testCopy_DuplicationIsolatesParent`
  + `testGame_RulesSeedAuthority`). Sibling sims start identically by design
  (documented AI-search limitation, never written back).
- Sole AI caller of a Rules helper (`SimulatedPlayerMCTS:282`) migrated to the
  non-Rules stream with identical candidate semantics.
- `TargetOptimization` prune stays on the non-Rules stream (heuristic enumeration
  limiting, never a card-mandated pick); card-mandated `TargetImpl.isRandom` picks
  use the game RNG.

## Setup order

See `WS54_SETUP_ORDER_ANALYSIS.md`. Declared deck-load order is the canonical
deterministic pre-shuffle sequence (`LinkedHashSet` preservation; identity semantics
=> multiplicity safe). No sorting on identity hash / UUID / memory address anywhere.

## Candidate order (section 18)

Every game-RNG `randomFromCollection` input is flow-ordered: library sequence,
battlefield `LinkedHashMap` insertion, `Players` seat order, `LinkedHashSet`
insertion, target-selection order, turn-ordered opponent lists, graveyard/hand/exile
zone order (`CardsImpl`-backed), EnumSet/enum order, sequential-int keys.
UUID-keyed `HashSet`/`HashMap` iteration is banned as a candidate order. Per-site
attestation: `WS54_RULES_RNG_CALLSITE_CLOSURE.json`.

## Match scope

`MatchImpl` owns a match-scoped `GameRandom` + `setMatchSeed/getMatchSeed/
isMatchSeedExplicit` for `shufflePlayers`. Never seeds/perturbs any game stream.

## Snapshot disposition

`ARBITRARY_SNAPSHOT_RESTORE_REPLAY = NOT_QUALIFIED`: rollback restores state, not RNG
offset (forward-only consumption). Credited target is start-to-finish seeded semantic
reexecution. See `WS54_SNAPSHOT_REPLAY_DISPOSITION.md`.

## Concurrency

`synchronized` GameRandom entry points (defense in depth); consumption order owned by
the single-threaded game lifecycle; no parallel-stream RNG consumption in Rules paths
(grep gate in closure file).

## Legacy surface

No-arg `Library.shuffle()` kept as `@Deprecated` non-authoritative fallback (AI
hidden-info sampling + tests only). Terminal gate: zero references from the
production Rules surface (test + grep closure).
