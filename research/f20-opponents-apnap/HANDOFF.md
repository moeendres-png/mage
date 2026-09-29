# F-20: Game.getOpponents in APNAP order

Commander Simulator Next tracker: moeendres-png/commander-playtest-lab#330.
Author: Claude Opus 5.5 (Claude Code), 2026-09-29.

## Source lock
Base: the exact candidate pin `b19596980f2734496ea1896504253e1bdd2756dd` (head of Mage PR #16). Upstream master has the same code. Rules: CR 2026-09-25, 101.4.

## Defect
`Game.getOpponents(playerId, excludeLeaved)` streamed `getPlayerList()`.
- `CircularList`'s iterator starts at the list's current pointer, and that pointer moves with priority.
- So every "each opponent …" loop (743 call sites) began from an arbitrary player instead of APNAP order.
- Example: Tempt with Discovery cast by the active player asked the player just before the caster first.

## Fix (`Mage/src/main/java/mage/game/Game.java`)
- New default `getPlayerIdsInApnapOrder()`:
  - takes a copy of the static turn-order list;
  - sets current to the active player;
  - steps with `getNext()` / `getPrevious()` per `isTurnOrderReversed()`.
- `getOpponents` streams that order.
- The range and left-player filters are unchanged.

## Native evidence
- `org.mage.test.multiplayer.apnap.EachOpponentApnap{3,4,5}PTest`: Tempt with Discovery cast by the first, second and third player in turn order.
- A recording player asserts the order of the tempting-offer questions. The expected order is derived from the scheduled turn order, which the casts on those turns prove.
- Results:
  - red on the pin: 9/9;
  - green with the fix: 9/9;
  - full `Mage.Tests` offline (`-pl Mage,Mage.Tests`): **6938 run, 0 failures, 0 errors, 125 skipped** (the pin baseline of 6929 plus these 9).

## Not done here
No Lab repin. Lab `XmageMultiplayerTemptingOfferTest.opponentsAreOfferedInApnapOrder` stays disabled until a repin admits this commit.
