# WS211 NEGATIVE_CONTROLS (DIRECTLY_VERIFIED)

- DUPLICATE_REQUEST_HANDLING = DEDUP_NO_CORRUPTION: `setConcedingPlayer`
  twice + `concede` for the same actor before processing => single leave,
  single winner, second `checkConcede` drain is a no-op. (2P + 4P green.)
- STALE_LOST_LEFT_ACTOR_HANDLING = FAIL_CLOSED: post-fix `Game.concede`
  rejects already-left/lost/won/drew/quit actors. Pre-fix runtime
  characterization PROVED a defect: stale post-game `concede(winner)` set
  `loses=true` on the winner (winner flag corrupted); post-fix the same test
  asserts winner intact. Remediation is the `!canConcede` guard on the
  external seam only; `Player.concede`/`setConcedingPlayer`/quit/timeout/
  forced-loss flows untouched.
- UNKNOWN_ACTOR_HANDLING = FAIL_CLOSED: random UUID (and null) =>
  `canConcede` false, `concede` ignored, no exception, game untouched.
- GAME_VS_MATCH_SEMANTICS = PRESERVED: `quit`/`timerTimeout`/`idleTimeout`
  keep their own flags and match-level meaning; the generic CONCEDE action
  is voluntary game concession only. No shared-path behavior changed.
- RULES_RNG_CONSUMPTION = ZERO: `getRulesRandomCalls()` identical across
  50x `canConcede` enumeration for all actors + unknown (life/hand/stack
  also unchanged), and across concede+`checkConcede` execution.
- Game-end boundary: post-game `canConcede` false for every actor;
  `concede` post-game ignored. No resurrection, no double winners.
