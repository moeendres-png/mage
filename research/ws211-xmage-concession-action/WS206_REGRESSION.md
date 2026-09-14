# WS211 WS206_REGRESSION

WS206 base preserved: HEAD remains a9b9a4075f6f92b2ec1ba03557674b2bbd33d9fc;
WS206 touched only `CombatGroup.java` + its tests; WS211 touches only
`Game.java`/`GameImpl.java` concession paths. No shared production code.

WS206_COMBAT_REGRESSION status:-impact CLEAR, tests PRE-BROKEN at base.

- `WS206TrampleReproducerTest` + `WS206CombatDamageMatrixTest` (13 tests):
  2 failures with WS211 applied. Re-verified at PRISTINE base via
  `git stash -u` round-trip (worktree = audit base, no WS211 content):
  IDENTICAL 2 failures (choice-count assertions, zero concede references
  in those tests; WS211 diff cannot execute on that path). Pre-existing,
  unrelated to WS211. Not reopened beyond this impact check per contract.
- Concede-adjacent + multiplayer + WS54 suites with WS211 applied:
  66/66 green (PlayerLeavesGame, Range1/RangeAll, PlayerLeft,
  WS54SeededReexecution incl. concede-divergence control, stack-target,
  continuous-effects, AngelOfSerenity, EndOfTurnMulti, ShareTheSpoils,
  WorldEnchantments, Saheeli).
- Mage module units: 112/112 green.
- WS206_BASE_PRESERVED = TRUE (source lock intact; no combat code touched).

FULL107 = NOT_RUN (per contract scope).
Checkstyle = NOT_RUN (maven-checkstyle-plugin unresolvable offline;
does not block semantic completion per contract).
