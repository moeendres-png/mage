# F-18: simultaneous Commander-zone choices in APNAP order

Commander Simulator Next tracker: moeendres-png/commander-playtest-lab#317.
Author: Claude Opus 5.5 (Claude Code), 2026-09-29.

## Source lock
- Base: the exact candidate pin `b19596980f2734496ea1896504253e1bdd2756dd` (tree `04c00f25bb456227b3c6d2996357b6d6d794a956`, head of Mage PR #16). Not master.
- Rules: CR 2026-09-25 (sha256 `8d860e45…`), rules 101.4, 704.3, 704.6d, 903.9a.

## Defect
`GameImpl.checkStateBasedActions` handled the Commander graveyard/exile state-based action as a per-player loop over `state.getPlayers().values()`. That produced two errors:
- owners were asked in seat insertion order, not APNAP;
- each owner's selected commanders were moved before the next owner chose, although this is one simultaneous state-based action.

## Fix (engine-native, `Mage/src/main/java/mage/game/GameImpl.java`)
- **Ordering.** New `getPlayersInApnapOrderIncludingLeft()`:
  - starts from a copy of the game's static turn-order `PlayerList` at the active player;
  - steps with `getNext()` / `getPrevious()` according to `isTurnOrderReversed()`;
  - keeps players who left in their turn-order position, so the same players as before are visited.
- **Collect, then move.** All choices are collected into an ordered map, and the selected commanders are moved only afterwards.
- **Unchanged.** `CommanderShouldStay` handling, prompts and single-owner behaviour.

## Native evidence (`Mage.Tests`, package `org.mage.test.commander.multiplayer`)
- Test classes: `CommanderZoneApnap{3,4,5,6}PTest` on `CommanderZoneApnapTestBase`.
- Each player count runs three scenarios:
  - Wrath of God with the first player active (graveyard path);
  - Final Judgment with the second player in turn order active (exile path);
  - a single-owner regression.
- Mixed choices: odd seats move, even seats leave, and seat B has partners Rograkh + Ardenn with mixed choices.
- A recording `TestPlayer` asserts the ask order, and asserts that no commander reached a command zone before every owner chose.
- The expected order is derived from each commander's successful cast on its owner's turn, not from `PlayerList`.

## Results
- Red on the pin: 8/8 multi-owner scenarios fail (seat order).
- Green with the fix: 12/12.
- Mutation (APNAP kept, moves made sequentially again): killed by the simultaneity assertion.
- Full `Mage.Tests`, offline, with `-pl Mage,Mage.Tests`: **6941 run, 0 failures, 125 skipped, 255 errors**.
  - Every error is `NoClassDefFoundError: org/mage/test/serverside/base/CustomTestCard`. That class is absent from this checkout and the offline classpath, and the same tests error identically on the unpatched pin. This is environmental.
  - For comparison, RG-06A CI at the pin reported 6929 run / 0 / 0 / 125.

## Not done here (separate workstream)
- No Lab repin.
- Lab `XmageMultiplayerCommanderZoneChoiceTest` keeps its disabled APNAP expectation until a repin moves the Lab onto an engine containing this commit and re-runs it through the Lab external-control path.
- Upstream report / PR: optional, after project acceptance.
