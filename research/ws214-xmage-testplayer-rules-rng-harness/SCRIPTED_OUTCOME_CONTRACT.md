# WS214 Scripted-Outcome Contract (adjudicated, preserved)

TestPlayer exists to make synthetic test decisions possible. Explicitly queued
choices are authoritative test input:

- `setFlipCoinResult(player, boolean)` -> choices queue `FLIPCOIN_RESULT_TRUE/FALSE`;
  `flipCoinResult` returns the queued boolean verbatim.
- `setDieRollResult(player, int)` -> choices queue `DIE_ROLL + result`;
  `rollDieResult` returns the queued int verbatim.

SCRIPTED_PATH_RULES_RNG_CONSUMPTION = NO (zero):
- Pre-fix source: scripted branches return before any RNG call.
- Proven at runtime pre-fix (t1/t2 PASS with calls==0) and post-fix
  (t1/t2 PASS with calls==0).
- `choicesRemoveCurrent` performs list removal + telemetry only; no RNG.

Contract preserved by the fix: the mutation touches only the UNSCRIPTED
fallback lines; scripted branches are byte-identical before/after.
SCRIPTED_COIN_PRECEDENCE = YES. SCRIPTED_DIE_PRECEDENCE = YES.
Live-game scripted suites still green post-fix: FlipCoinTest 3/3,
RollDiceTest 29/29 (includes Krark's Thumb / planar / strict-mode tests).
