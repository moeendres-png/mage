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