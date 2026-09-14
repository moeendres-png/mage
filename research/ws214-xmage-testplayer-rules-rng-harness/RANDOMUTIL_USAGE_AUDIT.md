# WS214 TestPlayer RandomUtil Usage Audit (machine-readable inventory)

Pre-fix `RandomUtil` occurrences in
`Mage.Tests/src/test/java/org/mage/test/player/TestPlayer.java` (full-file sweep;
no `Math.random` / `new Random` / `SecureRandom` / `ThreadLocalRandom` /
`Collections.shuffle` / `getRandom` anywhere in the file):

| # | file | method | call | purpose | classification | mutation_required | reason |
|---|------|--------|------|---------|----------------|-------------------|--------|
| 1 | TestPlayer.java:3658 (pre-fix) | flipCoinResult | RandomUtil.nextBoolean() | unscripted coin fallback | RULES_RANDOMNESS | YES | Magic coin flip is Rules-random; production PlayerImpl:3195 uses game.getRulesRandom().nextBoolean() |
| 2 | TestPlayer.java:3679 (pre-fix) | rollDieResult | RandomUtil.nextInt(sides)+1 | unscripted die fallback | RULES_RANDOMNESS | YES | Magic die roll is Rules-random; production PlayerImpl:3226 uses game.getRulesRandom().nextInt(sides)+1 |

Non-RandomUtil randomness-adjacent TestPlayer methods (all delegate to the
production `computerPlayer`, therefore already on the game Rules stream —
leave alone):
- flipCoin / flipCoins / rollDice / shuffleLibrary / shuffleCardsToLibrary /
  discardToMax / discardOne / discard(...) / searchLibrary / seekCard /
  getRandomToDiscard path (via PlayerImpl) — NON_RULES_TEST_INFRASTRUCTURE n/a,
  no direct RNG call in TestPlayer; no mutation.
- Scripted choice queue (`choices`, FLIPCOIN_RESULT_TRUE/FALSE, DIE_ROLL,
  setFlipCoinResult/setDieRollResult via CardTestPlayerAPIImpl) —
  SCRIPTED_TEST_INPUT; authoritative synthetic input, consumes no RNG
  (see SCRIPTED_OUTCOME_CONTRACT.md); no mutation.

OTHER_TESTPLAYER_RANDOMUTIL_RULES_USES = NONE beyond the two fixed fallbacks.
Post-fix `RandomUtil` occurrences in TestPlayer.java: ZERO (import removed;
only two code comments mention the stream by name).
