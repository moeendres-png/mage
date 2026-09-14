# WS206 Trample Validation (CR 702.19b + 510.1e)

Production change: `Mage/src/main/java/mage/game/combat/CombatGroup.java` only.
No Player interface/implementation change (seam preserved).

## What changed

1. `blockerDamage` trample branch: the single
   `player.getMultiAmountWithIndividualConstraints(..., damage-remaining, damage, ...)`
   call is now `requestLegalTrampleBlockerAssignment(...)`, which:
   - accepts a candidate only if `MultiAmountType.isGoodValues` passes AND, when
     `through = damage - sum > 0`, every non-null blocker satisfies
     `amount[i] >= blocker.getLethalDamage(attackerId, game)` (freshly computed, so
     already-marked + earlier same-step assignments + deathtouch count; protection/
     prevention never lower it);
   - zero through-damage accepts any division summing to damage (free, per 702.19b);
   - otherwise informs the choosing player and re-requests (max 5 attempts total),
     then falls back to the legal-by-construction defaults (lethal each in order,
     remainder tramples; or all-to-blockers summing to damage when nothing can
     trample). Illegal data is never executed.
2. `blockerDamage` non-trample branch and `attackerDamage` (CR 510.1c/d free division):
   wrapped in `requestLegalFreeBlockerAssignment(...)` — same re-request/fallback, but
   the only legality is the total (`isGoodValues` with totalMin=totalMax=damage). No
   ordering introduced.
3. Mapping hardened: assignments map via the non-null permanent order with a
   size-equality guard (previously indexed `blockersCopy`/`attackersCopy` against a
   possibly shorter `amounts`, including null-permanent misalignment). Behavior is
   identical when all permanents are present. Empty-division `get(0)` guards added.
4. Null-Player guards return legal defaults instead of NPE.

## Why this is the minimal systemic fix

- Reuses the authoritative `Permanent.getLethalDamage` (toughness/power-filter minus
  marked; deathtouch 1; loyalty/defense caps) — no duplicated lethal logic.
- Banding controller routing untouched: validation applies to whoever legally chose
  (attacker controller, or defending player under 702.22j; attacking player under 702.22k).
- First/double-strike scoping untouched: validation runs inside the per-step
  (`first`-flagged) assignment that already gates `dealsDamageThisStep` + FirstStrikeWatcher.
- No card-name logic, no UI-default-as-authority, no pilot trust: hostile totals and
  hostile per-blocker values are both rejected engine-side.

## Proven behavior

- Illegal through-damage cannot execute: reproducer 4/0+2 rejected pre-execution
  (re-request observed); protection-shape 0/3+3 rejected; both fall through to legal retries.
- Legal classes preserved: lethal-each-plus-through (2/2+2), zero-through free (6/0+0),
  deathtouch-minimal (1/1+4), marked-reduced (2/2+2 on 4-marked Crab), protection-minimal
  (1/2+3). See ACTUAL_CARD_MATRIX.md.
- Defaults stay legal: ComputerPlayer (Outcome.Damage => defaults) yields lethal-each;
  Human disconnect yields defaults; StubPlayer null yields defaults after bounded retries.

TRAMPLE_MULTI_BLOCKER_LEGALITY = PASS. TRAMPLE_ILLEGAL_THROUGH_DAMAGE_REJECTED = PASS.
TRAMPLE_NO_THROUGH_FREE_DISTRIBUTION = PASS.
