# WS214 TestPlayer Reachability Audit — TEST_ONLY

Affected implementation: `Mage.Tests/src/test/java/org/mage/test/player/TestPlayer.java`
(`flipCoinResult` L~3643, `rollDieResult` L~3667 pre-fix).

Classification: TEST_ONLY.

Evidence:
1. File lives under `Mage.Tests/src/test/java` (test sourceset; never packaged
   into production artifacts).
2. Production-main sweep for `mage.test.player` / `TestPlayer` references:
   - `Mage/src/main`: only two comment mentions
     (`Player.java:49` "- TestPlayer (support unit tests)",
     `PlayerImpl.java:5615` "// only used for TestPlayer to preSet Targets").
     Zero imports, zero instantiations.
   - `Mage.Sets/src`: zero matches.
   - `Mage.Server/src/main`: zero matches.
   - All concrete `org.mage.test.player.TestPlayer` importers resolve under
     `Mage.Tests/src/test` (harness + card tests).
3. `TestComputerPlayer` / `TestComputerPlayer7` / `TestComputerPlayerMonteCarlo`
   (the `computerPlayer` delegates) likewise live under `Mage.Tests/src/test`.
   `ComputerPlayer` itself (production AI) extends `PlayerImpl` and does NOT
   override `flipCoinResult` / `rollDieResult`, so the production delegate path
   is exactly `PlayerImpl` game-Rules logic.

Verdict: TESTPLAYER_PRODUCTION_REACHABLE = NO. No SCOPE_GATE. Test-only
mutation permitted; no production change made (see production-mutation guard).
