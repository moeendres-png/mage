# WS214 Unscripted Rules-RNG Contract (implemented)

When no scripted result exists and TestPlayer must resolve a Magic
Rules-random event, it now uses the authoritative game stream through the
exact production algorithm:

- `flipCoinResult`: `return game.getRulesRandom().nextBoolean();`
  (identical to `PlayerImpl.flipCoinResult`, Mage/src/main PlayerImpl:3195).
- `rollDieResult`: `return game.getRulesRandom().nextInt(sides) + 1;`
  (identical to `PlayerImpl.rollDieResult`, PlayerImpl:3226).

Design decision (recorded): direct `game.getRulesRandom()` was chosen over
delegating to `computerPlayer.flipCoinResult/rollDieResult` because
`TestComputerPlayer` routes those calls back to `testPlayerLink` in
harness-driven (non-computer) mode, which would recurse instead of reaching
the production algorithm. The chosen form is the smallest test-only change
with bit-identical stream semantics (proven by t7 + probe ctrl equality).

- No alternate coin/die implementation duplicated.
- No `RandomUtil` remains for Rules-random outcomes (zero occurrences).
- UNSCRIPTED_PATH_RULES_RNG_CONSUMPTION = YES (one Rules gate per draw).
- FLIP_COIN_UNSCRIPTED_RULES_RNG = YES. ROLL_DIE_UNSCRIPTED_RULES_RNG = YES.
