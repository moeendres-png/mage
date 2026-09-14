# WS206 Final Handoff — XMage Current-Rules Combat-Damage Hardening

## Source Lock

- repository: moeendres-png/mage
- branch: ws206/xmage-combat-damage-cr510-hardening-20260914
- AUDIT_BASE_SHA: cfc36f445f917f101fa2ed588770e043f53bc44c
- AUDIT_BASE_TREE: e51ba998d35decff087b5bebfdc001e62e8d33e4
- HEAD at handoff: see commit evidence (local only until push step below)
- worktree clean except the listed change set; WS204/Lab read-only respected.

## Work Completed

1. Bound current official Rules (TXT 20260819, effective 2026-08-07).
2. XHIGH read-first adjudication of the full combat-damage path (12 questions persisted).
3. Proved the suspected trample defect with an actual-card reproducer (BUG_CONFIRMED pre-fix).
4. Implemented the minimal Rules-Core correction in `CombatGroup` only: engine-side
   complete-assignment validation + bounded re-request + legal fallback; seam preserved.
5. Built a 13-test actual-card matrix covering all 8 required categories.
6. Ran affected regressions (58-test combat batch + 18-test adjacent/prior batch), all green.
7. Sealed the WS206 evidence namespace + Lab successor spec (not executed).

## New Findings

- WS204_COMBAT_DAMAGE_NO_PLAYER_HOOK is superseded: `blockerDamage`/`attackerDamage`
  already route through the generic `Player.getMultiAmountWithIndividualConstraints` seam.
- The seam passes totals but not cross-option trample legality — the engine never
  validated it, so illegal through-damage executed. Now fixed engine-side.
- No reachable damage-assignment-order logic exists (only dead log code + stale comment).
- Narrow approximation (documented, safe): prevented/wither-shared simultaneous
  visibility over-requires; never executes illegal data.

## Changes

- `Mage/src/main/java/mage/game/combat/CombatGroup.java` (+160/-13): validated
  trample + free-division assignment paths, bounded re-request (5), legal fallback,
  null/empty guards, misalignment-safe mapping. No API change.
- `Mage.Tests/.../ws206/WS206TrampleReproducerTest.java` (new, 1 test).
- `Mage.Tests/.../ws206/WS206CombatDamageMatrixTest.java` (new, 12 tests).
- `research/ws206-xmage-combat-damage-cr510/` (new evidence namespace, 11 files).

## Tests / Evidence

- New actual-card: 13/13 PASS.
- Existing combat/trample/banding/first-strike/multi-blocker: 58/58 PASS.
- Adjacent multi-amount + WS81/83/85: 18/18 PASS.
- Compile: PASS. Checkstyle: NOT_RUN (plugin unresolvable offline). FULL107: NOT_RUN.

## PASS / FAIL / UNKNOWN

- PRE_FIX_REPRODUCER = BUG_CONFIRMED (then fixed).
- COMBAT_DAMAGE_RULES_CORRECTNESS = PASS (bounded matrix scope).
- COMBAT_DAMAGE_EXTERNAL_SEAM = PRESENT.
- SIMULTANEOUS_ASSIGNMENT_ACCOUNTING = PASS (common) / APPROXIMATION (narrow, documented).
- Everything else claimed = PASS; FULL107 + checkstyle = NOT_RUN/UNKNOWN (explicitly not claimed).

## Remaining Blockers

- None for the bounded scope. Push + remote proof is the next action (below).

## Outputs

- Engine candidate commit (local) + WS206 evidence namespace + Lab successor spec.

## Dependencies Unblocked

- Coordinator can consume the candidate for the Lab repin successor; no WS204/WS205 reopen.

## Exact Next Action

- Canonical safe_push dry-run then actual push to
  ws206/xmage-combat-damage-cr510-hardening-20260914 (expected repo moeendres-png/mage,
  audit-base ref ws85/xmage-cr61412-future-state-hardening-20260913), then fetch and prove
  exact remote HEAD/tree + clean worktree. No raw git push. No PR. No merge.

## Terminal fields

WS206_XMAGE_COMBAT_DAMAGE_CR510 = COMPLETE
SOURCE_LOCK = PASS (cfc36f445f917f101fa2ed588770e043f53bc44c / e51ba998d35decff087b5bebfdc001e62e8d33e4)
CURRENT_OFFICIAL_RULES_VERSION = TXT 20260819 effective 2026-08-07 (official Magic Rules page)
CR510_1C_FREE_DISTRIBUTION = PASS
CR510_1D_MULTI_ATTACKER_BLOCKER_DISTRIBUTION = PASS
CR510_1E_COMPLETE_ASSIGNMENT_VALIDATION = PASS
DAMAGE_ASSIGNMENT_ORDER_PRESENT = NO
TRAMPLE_MULTI_BLOCKER_LEGALITY = PASS
TRAMPLE_ILLEGAL_THROUGH_DAMAGE_REJECTED = PASS
TRAMPLE_NO_THROUGH_FREE_DISTRIBUTION = PASS
DAMAGE_ALREADY_MARKED = PASS
SIMULTANEOUS_ASSIGNMENT_ACCOUNTING = PASS_WITH_DOCUMENTED_NARROW_APPROXIMATION
DEATHTOUCH_TRAMPLE = PASS
PROTECTION_PREVENTION_LETHAL = PASS
BANDING_ASSIGNMENT_CONTROLLER = PASS
FIRST_STRIKE = PASS
DOUBLE_STRIKE = PASS
PLAYER_MULTI_AMOUNT_SEAM = PRESERVED
COMBAT_DAMAGE_EXTERNAL_SEAM = PRESENT
WS204_COMBAT_DAMAGE_NO_PLAYER_HOOK = SUPERSEDED_BY_FRESH_SOURCE_TRUTH
PRODUCTION_RULES_CORE_CHANGE = Mage/game/combat/CombatGroup.java validation+re-request only
ACTUAL_CARD_BEHAVIOR = PASS (13/13 actual-card)
NEW_RULES_GAPS = prevented/wither-shared simultaneous visibility over-requirement (documented; no illegal execution)
CONCESSION = OUT_OF_SCOPE
BEHAVIOR_CREDIT_CHANGE = 0
FULL107 = NOT_RUN
RAW_GIT_PUSH_USED = NO
ARCHITECTURE_FREEZE = NOT_CLAIMED
PRODUCTION_PROVIDER = NOT_SELECTED
