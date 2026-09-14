# WS206 Architecture Adjudication (XHIGH read-first, persisted before fix)

Inspected at pinned base (before any production edit): Combat, CombatGroup,
Player, PlayerImpl (abstract), HumanPlayer, ComputerPlayer, TestPlayer, StubPlayer,
ComputerPlayerControllableProxy, MultiAmountMessage, MultiAmountType, getMultiAmount,
getMultiAmountWithIndividualConstraints, Permanent.getLethalDamage (PermanentImpl),
TrampleAbility, DeathtouchAbility, BandingAbility/BandsWithOtherAbility,
FirstStrikeWatcher, CombatDamageStep, DamageDistributionTest, FirstStrikeTest,
BandingTest, DeathtouchTest, CanBlockMultipleCreaturesTest.

## 1. Exact structures for multiple-blocker damage assignment

- `CombatGroup`: one attacker group = `attackers` (normally 1) + `blockers` (N);
  one blocking group (`Combat.blockingGroups`, keyed by blocker) = 1 blocker + N attackers.
- `CombatDamageStep.beginStep`: all groups `assignDamageToBlockers(first)`, then all
  blocking groups `assignDamageToAttackers(first)`, then `applyDamage` for both.
- `PermanentImpl.getLethalDamage(attackerId, game)`: toughness (or power under
  power-for-lethality filters) minus `this.damage`; deathtouch => min(1, lethal);
  planeswalker => min(loyalty); battle => min(defense). Ignores protection/prevention.
- Choice encoding: `MultiAmountMessage(min=0, max=damage, default=lethal-capped)` per
  option + `MultiAmountType` dialogue with `totalMin/totalMax`; decided through
  `Player.getMultiAmountWithIndividualConstraints`.

## 2. Does the generic multi-amount seam express every legal distribution?

PARTIAL by design, sufficient as a discretionary seam. Any distribution is encodable as
values (per-option 0..damage; totals damage..damage, or lethalSum..damage for trample),
but `MultiAmountType.isGoodValues` checks only per-option ranges + total range — never
cross-option trample legality (per-blocker lethal when through > 0). Legality therefore
belongs in the engine, not the seam. No Player API change is needed (see 12).

## 3. Who validates the returned complete distribution?

PRE_FIX: nobody on the combat path. HumanPlayer/TestPlayer enforce only `isGoodValues`;
ComputerPlayer returns legal-by-construction defaults; `CombatGroup.blockerDamage` and
`attackerDamage` execute `amounts` directly (trample remainder goes to the defender).
An illegal trample-through distribution that passes the total check executes. DEFECT.

## 4. Can an illegal trample-through assignment currently be returned and executed?

YES (proven, not assumed). 6/6 trample vs 2/2+2/2 with 4 to A + 0 to B + 2 through sums
to totalMin=4, passes `isGoodValues`, and pre-fix executed as-is (B 4/dies, Lion 0/lives,
defender -2). See PRE_FIX_REPRODUCER.md. POST_FIX the engine rejects/re-requests it.

## 5. Are legal non-trample all-to-one distributions allowed?

YES, pre- and post-fix. Non-trample uses totalMin=totalMax=damage with per-option 0..damage,
so (damage,0), (0,damage), and any split pass and execute. No lethal ordering. Preserved.

## 6. Any production-reachable old damage-assignment-order restriction?

NO. `rg` over production source finds no `pickBlockerOrder`/order-based legality.
`CombatGroup.logDamageAssignmentOrder` is private dead code (never called) — classified
DISPLAY_ONLY/UNREACHABLE_LEGACY, left untouched per "do not rename harmless symbols".
One TODO comment mentions `pickBlockerOrder` in passing; card names containing "Order"
(Order of Midnight, False Orders, Silkenfist Order), mana-payment priority order, and
Gollum "put back in any order" are UNRELATED. Full table in DAMAGE_ASSIGNMENT_ORDER_AUDIT.md.
DAMAGE_ASSIGNMENT_ORDER_PRESENT = NO (no reachable obsolete legality).

## 7. Simultaneous same-step assigned damage accounting

APPROXIMATED CORRECTLY for the common case. `doDamage(..., markDamage=true)` increments
`this.damage` immediately for normal damage, so later groups' `getLethalDamage` see earlier
same-step assignments (sequential processing with visible marks can realize any simultaneous
distribution since one player controls all of one side). Known narrow approximation: assignments
that never increment `this.damage` — prevented damage (protection) and wither-style deferred
counters — are invisible to later groups sharing the same blocker, causing over-requirement
(still legal, never illegal execution). Recorded as a gap, not a gate; no broad combat-phase
surgery in this workstream.

## 8. Deathtouch

CORRECT. `getLethalDamage` returns min(1, remaining) vs a deathtouch attacker, matching
702.2c. Engine defaults (1 per blocker) are the minimal legal trample shape; validation
enforces >= 1 per blocker when through > 0.

## 9. Already-marked damage

CORRECT. `getLethalDamage` subtracts `this.damage` (actual marked damage, including
pre-combat spells and earlier same-step assignments). Proven by
`testTrampleAlreadyMarkedDamage` (Crab 1/6 with 4 marked needs only 2 more).

## 10. Protection/prevention for lethal assignment

CORRECT (must not lower requirement). `getLethalDamage` uses toughness only and never
consults protection/prevention, matching the 702.19b protection example. Proven by
`testTrampleProtectionStillRequiresLethal` (1 must still be assigned to the 2/1
protection-from-green Lynx before any through-damage).

## 11. Banding controller exceptions

CORRECT and preserved. `defenderAssignsCombatDamage` (702.22j incl. Defensive Formation)
routes attacker-damage choice to the defending player; `attackerAssignsCombatDamage`
(702.22k) routes blocker-damage choice to the attacking player. Not confused with
assignment order. Proven by `testBandingDefenderChoosesVsTrample` + existing BandingTest 3/3.

## 12. Is any Player API change actually necessary?

NO. The generic `getMultiAmountWithIndividualConstraints` seam stays exactly as-is across
every Player implementation (Human/Computer/Test/Proxy/Stub untouched). WS206 adds only
engine-side validation + bounded re-request + legal-by-construction fallback inside
`CombatGroup` (Rules Core). No Commander-Lab concepts enter XMage.

Technical decisions recorded: (a) no API change; (b) 5-attempt bounded re-request with
`game.informPlayer` notices, then legal-default fallback (never execute illegal data);
(c) lethal reused from `Permanent.getLethalDamage`, never duplicated; (d) dead
`logDamageAssignmentOrder` left untouched; (e) protection/wither sharing approximation
documented as gap, not gate.
