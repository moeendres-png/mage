# WS211 FINAL_HANDOFF

## Source Lock

moeendres-png/mage @ ws211/xmage-authoritative-concession-action-20260914,
from AUDIT_BASE a9b9a4075f6f92b2ec1ba03557674b2bbd33d9fc (tree
8c7f8e4fd356352aee2e36c7ee3ff3e36cfc86e2). WS206 base preserved; no combat
code touched.

## Work Completed

- XHIGH read-first adjudication of the full concession surface (12 questions
  answered, persisted in state + ARCHITECTURE_ADJUDICATION.md).
- Rules authority verified live: CR-20260807 (effective 2026-08-07):
  104.3a concede-anytime; 723.6 controller-may-not / self-may-under-control.
- Action model decided: PLAYER_INITIATED_ACTION (WS204 blocking-callback
  proposal SUPERSEDED, bridge-side block preserved VALID).
- Minimal production change (2 files): `Game.canConcede(UUID)` availability
  predicate + `GameImpl` impl; stale guard on `Game.concede` (fixes runtime-
  proven winner-flag corruption on post-game stale requests). Internal
  quit/timeout/forced-loss/`setConcedingPlayer` flows untouched.
- 20 native tests (2P/4P/control/negatives/RNG), 20/20 green; 66/66
  concede-adjacent green; Mage 112/112 green.
- WS206 impact adjudicated: 2 failures pre-exist at pristine base (stash
  round-trip proof), unrelated.
- Evidence namespace (12 files) + execution-ready Lab successor spec sealed.

## New Findings

1. Stale `Game.concede(winner)` post-game set `loses=true` on the winner
   (hasWon flipped false) — remediated by the seam guard.
2. 2P `leave()` skips object cleanup once the game ends (intended early
   return); stack-cleanup proof therefore lives in the 4P test.
3. `controlPlayersTurn` refuses AI controllers (product limitation); tests
   establish identical native control fields directly.
4. canConcede/concede consume zero Rules RNG (counter-pinned).

## Changes

- M Mage/src/main/java/mage/game/Game.java (canConcede decl + javadoc)
- M Mage/src/main/java/mage/game/GameImpl.java (canConcede impl + concede guard)
- + Mage.Tests/.../serverside/ws211/ (3 test classes, 20 tests)
- + research/ws211-xmage-concession-action/ (12 evidence files)

## Tests / Evidence

See VALIDATION.md / VALIDATION.json. Checkstyle NOT_RUN (offline plugin),
FULL107 NOT_RUN, 3/5-player UNKNOWN (not claimed).

## PASS / FAIL / UNKNOWN

- Semantic COMPLETE criteria: all PASS except explicitly UNKNOWN items
  (3/5-player direct validation; mulligan/pre-game concede — harness starts
  post-mulligan) and NOT_RUN items above. No FAIL remains.

## Remaining Blockers

None in WS211 scope. Publication (push) pending — exact next action below.

## Outputs

WS211 Mage candidate (this branch head); evidence namespace; Lab successor spec.

## Dependencies Unblocked

Commander-Lab CONCEDE projection successor (spec sealed, not executed).

## Exact Next Action

Update state COMPLETE with truthful validated_head; checkpoint commit;
canonical safe_push dry-run then push to
ws211/xmage-authoritative-concession-action-20260914; prove remote
HEAD == local HEAD, remote TREE == local TREE, worktree clean.

## Terminal fields

WS211_XMAGE_AUTHORITATIVE_CONCESSION_ACTION = DELIVERED
SOURCE_LOCK = HELD (a9b9a4075f6f92b2ec1ba03557674b2bbd33d9fc)
WS206_BASE_PRESERVED = TRUE
CURRENT_OFFICIAL_RULES_VERSION = CR-20260807
CR104_3A_CONCEDE_ANY_TIME = CONFIRMED
CONTROLLED_PLAYER_SELF_CONCESSION = TRUE
TURN_CONTROLLER_CAN_CONCEDE_FOR_CONTROLLED_PLAYER = FALSE
CONCESSION_ACTION_MODEL = PLAYER_INITIATED_ACTION
CORE_AVAILABILITY_SURFACE = Game.canConcede(UUID)
NATIVE_GAME_CONCEDE_EXECUTION = Game.concede + setConcedingPlayer + checkConcede/leave (unchanged paths)
NON_PRIORITY_CONCESSION = PASS
STACK_NONEMPTY_CONCESSION = PASS
COMBAT_CONCESSION = PASS
FOUR_PLAYER_CONTINUATION = PASS
DUPLICATE_REQUEST_HANDLING = DEDUP_NO_CORRUPTION
STALE_LOST_LEFT_ACTOR_HANDLING = FAIL_CLOSED (guard added)
UNKNOWN_ACTOR_HANDLING = FAIL_CLOSED
RULES_RNG_CONSUMPTION = ZERO
GAME_VS_MATCH_SEMANTICS = PRESERVED
WS204_CONCESSION_BLOCKING_CALLBACK_REMEDIATION = SUPERSEDED_BY_FRESH_ARCHITECTURE_ADJUDICATION
WS204_BRIDGE_SIDE_CONCESSION_BLOCK = VALID_AT_WS204_SOURCE
WS206_COMBAT_REGRESSION = PRE_EXISTING_FAILURES_UNRELATED (2, identical at base)
PRODUCTION_RULES_CORE_CHANGE = canConcede + concede stale guard (2 files)
LAB_SUCCESSOR_SPEC = SEALED (not executed)
BEHAVIOR_CREDIT_CHANGE = 0
FULL107 = NOT_RUN
RAW_GIT_PUSH_USED = NO
ARCHITECTURE_FREEZE = NOT_CLAIMED
PRODUCTION_PROVIDER = NOT_SELECTED
