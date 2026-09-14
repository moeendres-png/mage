# WS212 WS211 Regression (narrow, concession preservation)

WS212 ships zero production diff, so the expected result is identity. Verified
with reactor-fresh artifacts (`mvn -pl Mage.Tests -am ...`):

- `WS211ConcessionActionTest`: 8/8 PASS.
- `WS211ConcessionAvailabilityTest`: 7/7 PASS.
- `WS211ConcessionMultiplayerTest`: 5/5 PASS.

`Game.canConcede` surface, guarded native concede semantics, player-initiated
action model, and multiplayer concession behavior: all preserved.
Concession availability still consumes zero Rules RNG (WS211 negative control
stands; WS212 consumer twins show no unexplained consumption drift).

`WS211_CONCESSION_REGRESSION = PASS (20/20)`.
`WS211_BASE_PRESERVED = YES`.
