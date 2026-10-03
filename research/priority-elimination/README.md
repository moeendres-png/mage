# Priority after state-based elimination (Lab #507)

Workstream: `XMAGE-SBA-ELIMINATION-PRIORITY-20261003`
Repository: `moeendres-png/mage`
Branch: `simulator/sba-elimination-priority-20261003`
Repair base: `103a1e0001ec7fb900ea03eddf345432b3ac31fe` (tree `f6a53692d1b7bf44feded88081049bd4f5776c1d`)

## 1. Defect

`GameImpl.playPriority` re-entered its per-player loop body after the state-based
action pass that 117.5 requires to happen before priority is handed over:

```
while (!player.isPassed() && player.canRespond() && ...) {   // eligibility read here
    checkStateAndTriggered();                                 // 704.5a may remove the player here
    applyEffects();
    saveState(false);
    if (isPaused() || checkIfGameIsOver()) { return; }
    if (player.priority(this)) { ... }                        // called on a departed player
}
```

`PlayerImpl.canRespond()` is false once the player left the game, but the
eligibility read happened before the state-based actions ran, so the engine still
asked a player that had just been eliminated for priority. Any player can be hit,
not only the active player: whoever holds priority and pays a lethal life cost,
loses the game between the two reads and is then prompted again.

Independently reproduced at runtime (see section 4), it matches the recorded
ELIM-TURN-3 tape pattern (departed player logged as lost, then a decision
requested from it in the same priority window).

## 2. Rules consulted

Official Comprehensive Rules, 2026-09-25 build,
<https://media.wizards.com/2026/downloads/MagicCompRules%2020260925.txt>,
SHA256 `8d860e451f20f38865b725b42d82feb714c725373dd8f3b32b8652b3eeb070ca`
(fetched read-only with `curl -sS -L`, HTTP 200, 977752 bytes, 9372 lines).

| Rule | Requirement, in own words |
| --- | --- |
| 117.5 | State-based actions, then triggered abilities, are performed and repeated **before** the player who was about to receive priority actually receives it. So the player about to act can be removed by that pass. |
| 704.5a | A player whose life total is 0 or less loses the game. |
| 118.3b | Paying life as a cost subtracts that life from the payer's life total. |
| 800.4a | When a player leaves, the priority they held passes to the next player in turn order who is still in the game. Objects they own leave the game and stack objects they control cease to exist. |
| 800.4b | An object that would be put onto the battlefield under a departed player's control stays where it is. |
| 800.4j | A player leaving during their own turn does not abort that turn: it completes without an active player, and priority goes to the next player in turn order. |

No long rule text is duplicated here; the fetched file above is the reference.

## 3. Repair

`Mage/src/main/java/mage/game/GameImpl.java`, `playPriority`, 7 added lines
inside the per-player loop, right after the state-based action pass and before
`player.priority(this)`:

```java
// 117.5. The state-based actions above run before the player receives priority, so the
// player can lose the game (e.g. 704.5a) or leave it in between. A player that left
// the game can't receive priority, so stop here and let the players loop below move
// on to the next player in turn order who is still in the game (800.4a, 800.4j).
if (!player.canRespond()) {
    break;
}
```

`break` leaves only the innermost per-player loop, so control falls through the
existing post-loop path (`resetShortLivingLKI`, `allPassed`, resolve-or-return) and
then `state.getPlayerList().getNext()`, which is the engine's existing mechanism
for handing the window to the next player in turn order. Turn progression for a
departed active player already worked before this repair and is now asserted rather
than assumed. No new rules core, no adapter, no harness-side legality.

## 4. Evidence

Test class: `Mage.Tests/src/test/java/org/mage/test/multiplayer/PriorityEliminationTest.java`
(SHA256 `d0db25fe09782606607fcfc75e01542d5faa062de62074a72e71550c0a6a5996`).

Instrumentation is observational only: a `TestPlayer` subclass records every
`Player.priority(game)` call the engine makes together with the recorded player's
game status at that moment. It never changes engine behaviour and no outcome is
injected - every elimination comes from a real life-payment cost (118.3b) driving
the life total to 0 and the engine's own 704.5a check removing the player.

Table size is chosen by a token in the test method name, because the harness
`@Before reset()` creates the game before the test body runs. Players are added in
the same order as the standard multiplayer bases (A, B, C, D, E). XMage's player
list is built in reverse insertion order and the cycle starts at the starting
player, which was confirmed with a throwaway probe (insert A, E, D, C, B produced
turn order A, B, C, D, E) and is asserted at runtime in every scenario:

| seats | turn order |
| --- | --- |
| 2 | A, B |
| 3 | A, C, B |
| 4 | A, D, C, B |
| 5 | A, E, D, C, B |

Commands (written to a logfile, Maven exit status reported separately, never
through a pipe):

```
MAVEN_OPTS="-Djava.io.tmpdir=$TMPDIR" mvn -o -pl Mage.Tests -am test \
  -Dtest='<selection>' -DfailIfNoTests=false -Dsurefire.failIfNoSpecifiedTests=false
```

`-am` keeps the engine classes coming from this reactor instead of the shared
`1.4.61` cache jar.

### Fail-before / pass-after matrix (whole class, same source of the test)

| Test | original `GameImpl` | repaired `GameImpl` | class |
| --- | --- | --- | --- |
| `test_fourPlayers_activePlayerEliminatedDuringOwnPriorityGetsNoPriority` | FAIL | PASS | regression, active player |
| `test_fourPlayers_nonActivePlayerEliminatedDuringPriorityGetsNoPriority` | FAIL | PASS | regression, non-active player |
| `test_fourPlayers_stackOfDepartedActivePlayerIsRemovedAndSurvivorStackObjectResolves` | FAIL | PASS | regression, stack + continuation |
| `test_threePlayers_activePlayerEliminatedDuringOwnPriorityGetsNoPriority` | FAIL | PASS | regression, 3 seats |
| `test_fivePlayers_activePlayerEliminatedDuringOwnPriorityGetsNoPriority` | FAIL | PASS | regression, 5 seats |
| `test_twoPlayers_departedPlayerGetsNoPriority` | PASS | PASS | coverage, see note |
| `test_fourPlayers_controlAllPlayersInGameReceivePriority` | PASS | PASS | control, all in game |
| `test_fourPlayers_controlNonLethalLifePaymentKeepsPriorityAndPlayerInGame` | PASS | PASS | control, non-lethal |

All five failures are the single intended assertion
`assertNoPriorityForDepartedPlayer`; no incidental failure occurred. Example red
message on the original source:

```
117.5/800.4a - engine requested priority from a player that already left the game:
    PlayerC|T3|PRECOMBAT_MAIN|inGame=false
```

with the same assertion failing for `PlayerB|T1`, `PlayerC|T2` and `PlayerC|T4`
in the 4-player, 3-player, 5-player and non-active variants.

Surefire counters (no skipped case is presented as coverage):

| run | tests | failures | errors | skipped |
| --- | --- | --- | --- | --- |
| original source, focused method | 1 | 1 | 0 | 0 |
| original source, whole class | 8 | 5 | 0 | 0 |
| repaired source, focused method | 1 | 0 | 0 | 0 |
| repaired source, whole class | 8 | 0 | 0 | 0 |

### Note on the two-player case

`test_twoPlayers_departedPlayerGetsNoPriority` is green on the original source and
is therefore **not** fail-before evidence. In a two-player table the elimination
makes `checkIfGameIsOver()` true inside the same state-based pass, and the existing
`if (isPaused() || checkIfGameIsOver()) return;` returns before `player.priority`.
The defect is unreachable at two seats, so this test is retained as coverage that
the repair does not change two-player behaviour, not as proof of the defect.

### Broader bounded runs on the repaired source

| selection | tests | failures | errors | skipped |
| --- | --- | --- | --- | --- |
| `PriorityEliminationTest`, `org.mage.test.multiplayer.**`, `org.mage.test.sba.**`, `org.mage.test.rollback.**`, `org.mage.test.turnmod.**`, `org.mage.test.game.**`, `org.mage.test.lki.**` | 123 | 0 | 0 | 0 |
| `org.mage.test.commander.**`, `org.mage.test.player.**`, `org.mage.test.mulligan.**`, `org.mage.test.deck.**`, `org.mage.test.AI.**` | 245 | 0 | 0 | 22 |

The 22 skips are pre-existing in that selection and are not counted as coverage.
Harness preflight: `PlayersListAndOrderTest` 6/6 on the original source.

## 5. Raw evidence

Raw Maven logs, surefire XML and a `SHA256SUMS` manifest for every run above are
kept outside the repository under
`$FOUNDRY_RUN_DIR/tmp/opencode/evidence/` (run-scoped scratch, not Git content):
`RED/`, `RED-class/`, `GREEN-focused/`, `GREEN-class/`, `GREEN-broad/`.

## 6. Scope limits

This is an ordinary engine repair. It is **not** Full107, AF06 or AF08 evidence,
and no full-game, deck, card-data or qualification claim is made or implied here.
Candidate pin and freeze decisions remain with the Coordinator.
## 7. Coordinator evidence persistence and impact adjudication

The exact raw logs and XML described above are also preserved in
`evidence/regression-evidence-20261003.zip`, alongside `EVIDENCE_SEAL.json` and
`SHA256SUMS`. The seal binds the unchanged engine/test sources to checkpoint
6fbf16fdc029b6b6dff6860003cdbc9d02ab4dca and lists all15 raw-file byte hashes.
Coordinator readback independently matched all8 test names between red and green,
confirmed the5 red failures have the intended departed-priority assertion, and
confirmed all8 repaired cases pass without skips. No contemporaneous original
compiled-bytecode hash was captured; that field remains explicitly UNKNOWN.

The Lab test-impact mapper flags this external Mage source surface as uncertain;
its default pytest commands apply to Lab and cannot validate this Java reactor.
Manual impact adjudication therefore requires the complete existing Mage.Tests
reactor signal on the published head plus exact-head independent review before
unqualified component validation. Existing focused evidence remains valid; broad
unrun coverage is UNKNOWN. Mage.Verify retains its separate semantic obligations
and inherited external-reference failures. Full107/AF06/AF08 credit remains
NOT_RUN until candidate-pin impact adjudication and affected requalification.

New Coordinator transition at Lab255 comment5968556784 (2026-10-03T11:05:55Z)
reserves further pre-Freeze campaign work to Claude and forbids new OpenCode
workstreams. The already-started Lab507 repair is handed over as an unmerged
draft; no C13/C14 or foreign implementation is taken over.

## 8. CI follow-up: MonarchTest.test_MonarchByDies fixture adaptation

Coordinator CI run 37119753436, job 111193455619, on exact head
`b0ebd84a52eb465fafced33db108ceeee16330ee` executed Mage.Tests with 6821 tests,
1 failure, 0 errors, 125 skips. The single failure was
`MonarchTest.test_MonarchByDies` at line 120:
`PlayerA must have 0 actions but found 1`. Mage.Verify was SKIPPED on that run,
so it carries no FAIL/PASS result.

Cause, derived from source and confirmed by a local reproduction on the exact
head: the fixture activated a custom 100 damage ability targeting PlayerA and
then called the global `waitStackResolved(1, PRECOMBAT_MAIN)` overload, which
queues a wait command for every seated player including PlayerA. After the
damage resolved, the real 704.5a state-based action eliminated PlayerA, and under
117.5 the repaired engine performs that state-based action before handing
priority over, so PlayerA is never asked for priority again and cannot consume
its queued wait command. The old engine consumed it through the very post-mortem
priority defect that section 1 describes. The monarch transfer to PlayerD and
`assertLostTheGame(playerA)` are unaffected and were kept unchanged.

Adaptation: observation ownership for the post-elimination wait moved to the
surviving players, using the existing per-player
`waitStackResolved(int, PhaseStep, TestPlayer)` overload. Nothing else in the
fixture changed, and no harness file was touched:

- `waitStackResolved(1, PRECOMBAT_MAIN)` after the lethal activation replaced by
  the same wait queued for playerB, playerC and playerD only.
- Added `checkStackSize("lethal damage ability pending", 1, PRECOMBAT_MAIN,
  playerA, 1)`, which observes the lethal damage ability pending on the stack
  while PlayerA still holds priority and is still in the game. This is an
  additional positive assertion, not a removal.
- Unchanged: the Thorn of the Black Rose cast, the "monarch to A" check, the
  "monarch to D" check on turn 2, `setStrictChooseMode(true)`, the stop point and
  `assertLostTheGame(playerA)`.

All three MonarchTest methods are the ordinary fixture control for this change.

### Local evidence for the fixture

| run | tests | fail | err | skip |
| --- | --- | --- | --- | --- |
| exact head b0ebd84, focused `MonarchTest#test_MonarchByDies` | 1 | 1 | 0 | 0 |
| adapted fixture, all `MonarchTest` methods | 3 | 0 | 0 | 0 |
| adapted fixture, designations + multiplayer + sba | 93 | 0 | 0 | 0 |

The focused red failure is exactly the CI failure:
`java.lang.AssertionError: Player PlayerA must have 0 actions but found 1` at
`MonarchTest.test_MonarchByDies(MonarchTest.java:120)`.

### Complete Mage.Tests reactor run after the fixture adaptation

Command (no `-Dtest`, so no case is selected away):

```
JAVA_TOOL_OPTIONS="-Djava.io.tmpdir=$TMPDIR" MAVEN_OPTS="-Djava.io.tmpdir=$TMPDIR" \
  mvn -o -pl Mage.Tests -am test
```

| run | tests | fail | err | skip |
| --- | --- | --- | --- | --- |
| first complete run | 6822 | 1 | 3 | 125 |
| same run with `JAVA_TOOL_OPTIONS` | 6822 | 0 | 0 | 125 |

The first complete run's 1 failure and 3 errors were all sandbox artifacts, not
code defects: `LoadCheatsTest.testCommands`, `DatabaseCompatibleTest.test_AuthUsers`,
`ZipFilesReadWriteTest.test_Read` and `ZipFilesReadWriteTest.test_write` all call
`File.createTempFile` / JUnit temp files, which resolve to `/tmp`, and `/tmp` is
read-only under the launcher sandbox. `MAVEN_OPTS` only reaches the Maven
launcher JVM, not the forked surefire JVM, so the fork also needs
`JAVA_TOOL_OPTIONS`. Re-running just those four cases with both variables set
passes them (5 tests, 0 failures, 1 pre-existing skip), and the complete run then
passes. None of these four cases touches priority, elimination or the stack.

Final aggregated counters, summed from all 1973 surefire XML files of that run:
**tests 6822, failures 0, errors 0, skipped 125**. The 125 skips are pre-existing
and spread over 69 classes (largest: `LoadTest` 10,
`DamageMultiLifelinkTriggerTest` 7, `SimulationPerformanceAITest` 7,
`AttackBlockRestrictionsTest` 5, `BecomeBlockTriggersMonteCarloAITest` 5). They
are recorded, not claimed as coverage.

Note on the count: local runs report 6822 tests where CI reported 6821. Coordinator readback resolves the difference: the local run includes one stale
compiled `ProbeTurnOrderTest` from the earlier removed throwaway source. It is
listed as one passing case in the XML manifest and receives no qualification
credit. The committed-source corpus has6821 cases; fresh CI rechecks that corpus.

Seal for this section: `evidence/monarch-fixture-evidence-20261003.zip` with
`EVIDENCE_SEAL_MONARCH.json` and `SHA256SUMS_MONARCH`.
