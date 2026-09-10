# WS54 Setup-Order Analysis

## The defect (pre-repair, DIRECTLY_VERIFIED)

`Deck.cards` is an insertion-ordered `LinkedHashSet` filled by `Deck.load` in
declared deck-list order (main, then sideboard). `getMaindeckCards()`
(`Deck.java:212-217`) re-collected it with `Collectors.toSet()` (HashSet),
destroying declared order. `PlayerImpl.useDeck:417` feeds that order into
`Library.addAll`, so the pre-shuffle library sequence depended on fresh per-run
card UUIDs. Same shape in `CardsImpl.getRandom:86-90` and `PlayerImpl.seekCard`.

Reproduced pre-repair: declared `[Plains x20, Island x20, Forest x20]` materialized
as e.g. `[Island,Plains,Forest,Plains,...]`; two fresh constructions diverged; the
same seed then shuffled different inputs to different outputs (R1-R3).

## The canonical pre-shuffle sequence (post-repair)

`getMaindeckCards()` now collects to `LinkedHashSet`: the declared deck-load order
is preserved 1:1 into `useDeck` -> `Library.addAll`. The choice is justified:

1. The deck list has a meaningful declared order (the list the player submitted);
   preserving it is not Magic legality, it is input fidelity.
2. Multiplicity is safe: cards are distinct objects with identity semantics
   (`CardImpl` defines no `equals`/`hashCode`; verified by grep), so no two physical
   cards ever collapse.
3. Randomness enters exactly once, at the Rules shuffle boundary
   (`Game.init` shuffle-all-libraries, mulligan shuffles, effect shuffles), through
   the game-scoped RNG.
4. No sorting on object-identity hash, transient UUID, JVM iteration order, memory
   address, or any process-specific value exists anywhere in the setup path.

Proven by `testP1_SetupMaterializationDeterministic` (25 fresh constructions,
exact equality with declared order) and `testP1_SameSeedFreshGamesSameShuffle`.

## Related materializations fixed the same way

- `CardsImpl.getRandom` candidate set: `LinkedHashSet` (collection flow order).
- `PlayerImpl.seekCard` candidate set: `LinkedHashSet` (library top-to-bottom order).
- `possibleTargets` implementations + `keepValidPossibleTargets` (21 target files):
  `LinkedHashSet` (source-traversal flow order).
- `AttackedThisTurnWatcher` sets: `LinkedHashSet` (attack-declaration order).
- `Counters` keySet copies (`MoveCounterTargetsEffect`): `LinkedHashSet` (String keys
  were already cross-run stable; now also flow-stable).
- `Camouflage.masterMap`: `LinkedHashMap` (defender flow order).
- `ChaosDefiler.permanents`: `LinkedHashSet` (turn order).
- `ZiatorasEnvoy.landSet`: `LinkedHashSet` (MDFC half order).
- `ExposeTheCulprit` moveCards input: `LinkedHashSet` (selection order).
- `Library/CardsImpl.getUniqueCards`: `LinkedHashMap` (flow order).

Single-candidate picks (`size < 2` fast path in `randomFromCollection`) and
player-choice fallbacks are order-independent by construction; attested per site in
`WS54_RULES_RNG_CALLSITE_CLOSURE.json`.

## What was NOT changed (and why)

- Card/player/game UUID generation stays random (`IDENTITY_ONLY_RANDOMNESS`): identity
  must stay unique; determinism comes from never keying candidate order on it.
- `getOpponents`/`getPlayersInRange` already return turn-ordered `LinkedHashSet`/
  `PlayerList`; `Battlefield.field` and `Players` are `LinkedHashMap`; hand/graveyard/
  exile zones are `CardsImpl` (insertion-ordered). No changes needed.
- `SeasonsBeatings` sequential-int keyed map: integer keys iterate ascending for any
  reachable size and are used as semantic indices, not iteration positions; unchanged.
- Booster/draft/tournament/collation/cosmetic ordering: out of the Commander
  constructed scope; unchanged and documented as infrastructure randomness.
