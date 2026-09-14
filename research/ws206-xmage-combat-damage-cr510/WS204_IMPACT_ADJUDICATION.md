# WS206 WS204 Impact Adjudication (superseding finding; WS204 artifacts untouched)

WS204_COMBAT_DAMAGE_NO_PLAYER_HOOK = SUPERSEDED_BY_FRESH_SOURCE_TRUTH.

- WS204's broad claim ("combat damage assignment is an XMage Core boundary because no
  Player hook exists") is contradicted by the pinned engine at cfc36f44:
  `CombatGroup.blockerDamage(...)` and `attackerDamage(...)` already call
  `Player.getMultiAmountWithIndividualConstraints(...)` for multiple-blocker and
  multiple-attacker damage distribution.
- Commander-Lab WS204 `XmageFullGamePlayer` already overrides exactly this generic
  Player method and converts it into external numeric decisions. The seam is therefore
  PRESENT for the multi-blocker/multi-attacker combat-damage path (single-blocker
  assignment requires no choice and correctly bypasses the seam).
- No WS204 file was read for mutation and none was modified in WS206. This finding
  supersedes; it does not rewrite history.

Independent seam verdict (fresh WS206 evidence):

- COMBAT_DAMAGE_EXTERNAL_SEAM = PRESENT (generic, discretionary-choice only).
  The seam expresses values, not legality: per-option ranges + total range pass through,
  cross-option trample legality is engine-owned (WS206 validates in `CombatGroup`).
  Human/Computer/Test/Proxy implementations are unchanged; StubPlayer (null-returning,
  non-combat test utility) is not production-reachable for combat and now degrades to
  legal defaults instead of NPE-adjacent behavior.

COMBAT_DAMAGE_RULES_CORRECTNESS (post-fix, bounded claim): PASS for the matrix scope
(non-trample free division; trample lethal/through/zero-through; marked; deathtouch;
protection/prevention non-lowering; banding controllers; first/double-strike scoping;
blocker-vs-attackers). Narrow documented approximation: prevented/wither-shared
simultaneous visibility (over-requirement only, never illegal execution). No
ENGINE_ARCHITECTURE gate opened: sequential-with-visible-marks remains systemically
sufficient for all independent cases completed here.
