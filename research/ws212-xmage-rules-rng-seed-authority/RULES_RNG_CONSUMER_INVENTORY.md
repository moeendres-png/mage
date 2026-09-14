# WS212 Rules-RNG Consumer Inventory (re-verified at WS211 HEAD)

Base: WS54 closure `research/ws54-xmage-rng-reexecution-remediation/
WS54_RULES_RNG_CALLSITE_CLOSURE.json` (`unknown_in_scope: 0`, 20 game-RNG sites,
8 allow-listed non-Rules sites). WS212 re-ran every closure gate statically at
this HEAD and runtime-proved the representatives below. No new production
Rules-random call sites were introduced between WS54 and this HEAD (the only
production diff in between is WS211 concession availability, which consumes zero
Rules RNG — see WS211 NEGATIVE_CONTROLS + WS212 WS211_REGRESSION).

## Static gate re-verification (this HEAD, CODE_DERIVED)

- `RandomUtil.nextInt/nextBoolean/nextDouble` in `Mage/src/main`: Rotater (booster
  collation), ChoiceImpl x2 (AI-only setRandomChoice), CardRepository/Sets
  (cosmetic), TournamentUtil/ExpansionSet/ReshuffledSet/DraftCube/TournamentImpl
  (sealed/draft/tournament infra), nextColor (cosmetic). All allow-listed. PASS.
- Same sweep in `Mage.Sets/src/mage/cards`: only `MagesContest:76` (AI bid guard,
  allow-listed). PASS.
- `Collections.shuffle` in engine+cards: game-scoped (`PlayerImpl` x2,
  5 card files) or match-scoped (`MatchImpl`); no-arg only in
  `RandomBoosterDraft:47`, `SwissPairing:45` (infra). PASS.
- 1-arg `randomFromCollection` (non-Rules): `TokenRepository` (cosmetic),
  `TargetOptimization` (AI heuristic) only. PASS.
- `parallelStream` in RNG paths: zero. PASS.

## Representative adjudication

| Consumer | Verdict | Basis |
|---|---|---|
| Initial library shuffle (`PlayerImpl.shuffleLibrary` → `Library.shuffle`) | RULES_RANDOM_CORRECT | Fresh-JVM twins + game twins |
| In-game shuffles (same `shuffleLibrary` path every shuffle effect calls) | RULES_RANDOM_CORRECT | Twin games (t4) |
| Choosing-player pick (`GameImpl.pickChoosingPlayer`) | RULES_RANDOM_CORRECT | Game twins (active player in digest) |
| London mulligan reshuffle (sole RNG: `shuffleLibrary`) | RULES_RANDOM_CORRECT | Code + shared qualified shuffle gate |
| Smoothed-London `drawHand` (Rules draws + shuffle) | RULES_RANDOM_CORRECT | Twin games (t7) |
| Coin flip (`PlayerImpl.flipCoinResult`) | RULES_RANDOM_CORRECT | Production-delegate twins (t5) |
| Die roll (`PlayerImpl.rollDieResult`) | RULES_RANDOM_CORRECT | Production-delegate twins (t5) |
| Random discard (`getRandomToDiscard` → `CardsImpl.getRandom`) | RULES_RANDOM_CORRECT | Twin games (t6) |
| Random target (`TargetImpl` isRandom → shared `randomFromCollection` gate, flow-ordered candidates) | RULES_RANDOM_CORRECT | Code audit + shared-gate runtime (t5/t6 same gate) |
| Random permanent/player selection (turn-ordered / LinkedHashMap candidates) | RULES_RANDOM_CORRECT | WS54 closure, gates re-verified |
| AI/UI/infra/cosmetic/product-gen `RandomUtil` sites | NON_RULES_RANDOM | Allow-list, storm-isolation tests |
| Remaining card-file sites in WS54 closure (49 files, per-site notes) | RULES_RANDOM_CORRECT | Closure + gate sweeps (no drift) |
| UNKNOWN in scope | 0 | — |

## New finding (harness-only, NOT production)

`TestPlayer.flipCoinResult` / `rollDieResult` (Mage.Tests harness) fall back to the
non-Rules `RandomUtil` stream when no scripted choice (`setFlipCoinResult` /
`setDieRollResult`) is set — production `PlayerImpl` consumes
`game.getRulesRandom()`. First witnessed as a WS212 t5 twin mismatch, classified
as test-harness artifact, production path qualified via the `computerPlayer`
delegate instead. No harness mutation in WS212 (shared-helper risk, out of
scope); recommended follow-up for a harness workstream: align the unscripted
fallback with production or fail loudly.

Machine-readable delta: RULES_RNG_CONSUMER_INVENTORY.json (this directory).
