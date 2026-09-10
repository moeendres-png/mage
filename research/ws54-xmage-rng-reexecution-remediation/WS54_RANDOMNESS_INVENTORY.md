# WS54 Randomness Inventory (source lock `0c1f455e`)

Method: systematic `rg` sweep for `RandomUtil`, `new Random`, `Collections.shuffle`,
`.shuffle(`, `ThreadLocalRandom`, `SecureRandom`, `Math.random`, `randomFromCollection`,
`getRandom(`, `flipCoin`, `rollDice`, `shuffleLibrary` across `Mage/src/main`,
`Mage.Sets/src`, AI server plugins, client/server infra. Every production-reachable
site read in context. Machine-readable closure: `WS54_RANDOMNESS_INVENTORY.json`.

## Totals

- RULES_RNG: 16 (sites/groups)
- SETUP_RULES_RNG: 4
- AI_RNG: 3
- UI_RNG: 1 (grouped with infra cosmetics)
- INFRASTRUCTURE_RNG: 5 (groups)
- TEST_RNG: 1 (group)
- IDENTITY_ONLY_RANDOMNESS: 1 (group)
- UNKNOWN: 0

## Headline topology (pre-repair)

1. `mage.util.RandomUtil` owns ONE static `java.util.Random` shared JVM-wide by every
   game, every AI search/simulation, and every Rules path (`RandomUtil.java:14`).
2. `Library.shuffle()` (the Fisher-Yates behind every library shuffle) takes no
   game/RNG argument; `PlayerImpl:1061,1204` use no-argument `Collections.shuffle`.
3. `Deck.getMaindeckCards()` (`Deck.java:212-217`) collects the ordered
   `LinkedHashSet` deck into a `HashSet` (`Collectors.toSet()`), destroying declared
   order before `PlayerImpl.useDeck:417` feeds it to the library. Same shape in
   `CardsImpl.getRandom:86-90` and `PlayerImpl.seekCard` (`Collectors.toSet()`).
4. AI players (`ComputerPlayer`, `SimulatedPlayerMCTS`, `ComputerPlayer6`) draw
   discretionary randomness from the same global stream; `SimulatedPlayerMCTS:282`
   is the sole AI caller of a game-Rules-consuming helper (`Cards.getRandom(game)`).
5. `GameImpl.pickChoosingPlayer:1569`, `MatchImpl.shufflePlayers:226`,
   `SmoothedLondonMulligan` mulligan smoothing, and ~55 card/booster `RandomUtil`
   sites complete the surface. Booster/draft/tournament/collation generation and
   cosmetic printing/image picks are sealed-product/infra randomness, unreachable
   in the Commander constructed pipeline (documented INFRASTRUCTURE_RNG, not migrated).
6. `RedElementalTrampleHasteToken` carries an unused `RandomUtil` import (no call site).
7. Identity: game/player/card UUIDs are fresh per construction (`IDENTITY_ONLY`).
   Consequence for section 18: candidate ordering must NEVER depend on UUID-keyed
   `HashSet`/`HashMap` iteration; use game-flow order (library sequence,
   `LinkedHashMap` battlefield insertion, `Players` seat order) or stable semantic keys.
   `Battlefield.field` is `LinkedHashMap`, `Players` is `LinkedHashMap` -- both yield
   deterministic flow order already.

## Reachability notes for the claimed Commander boundary

- In scope (migrate): all RULES_RNG + SETUP_RULES_RNG above, including the 5 no-arg
  card shuffles and the match seating shuffle (match-scoped seed).
- Out of scope (stay on non-Rules entropy, documented): booster/collation/draft/
  tournament/Swiss/Jumpstart generation, cosmetic printing/image selection, server
  session/key material, UI cosmetics, test-helper randomness.
- `ChoiceImpl.setRandomChoice` stays on the non-Rules stream: all callers are AI.
