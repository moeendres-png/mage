# WS211 VALIDATION

Offline: `mvn -o -pl Mage.Tests -am test` (reactor build from source).

| Suite | Result |
|---|---|
| WS211ConcessionActionTest (8, 2-player native) | 8/8 PASS |
| WS211ConcessionMultiplayerTest (5, 4-player native) | 5/5 PASS |
| WS211ConcessionAvailabilityTest (7, predicate + RNG + acceptance) | 7/7 PASS |
| WS211 total | 20/20 PASS |
| Concede-adjacent/multiplayer/WS54 (12 classes) | 66/66 PASS |
| Mage module units | 112/112 PASS |
| WS206 combat (impact check) | 2 pre-existing base failures, identical with/without WS211 (NOT caused by WS211) |
| Checkstyle | NOT_RUN (offline plugin unresolvable) |
| FULL107 | NOT_RUN |

Pre-change characterization (unmodified code): 4/8 action tests failed —
stale-winner corruption CONFIRMED (drove the `Game.concede` guard), plus 3
test-side assertion bugs of mine (winner `isInGame`, 2P stack-cleanup skip),
all corrected; final suite is 20/20 against the fixed engine.

Production diff: `Mage/.../game/Game.java` (+`canConcede` decl + javadoc),
`Mage/.../game/GameImpl.java` (+`canConcede` impl, +stale guard in `concede`).
No other production files touched.
