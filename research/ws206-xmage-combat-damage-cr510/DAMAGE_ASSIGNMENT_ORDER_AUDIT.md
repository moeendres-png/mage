# WS206 Damage Assignment Order Audit

Method: `rg -n` over production `Mage*/src/main/java` and `Mage.Tests` for
`pickBlockerOrder|blockerOrder|damageAssignmentOrder|DamageAssignment|assignedOrder|
chooseBlocker|selectBlockerOrder|damage assignment order|blocker order|lethal-before-next|
ordered blockers` (case-insensitive where relevant), plus manual review of
`CombatGroup.blockerDamage` / `attackerDamage` legality conditions.

## Findings

| Occurrence | Location | Classification | Rationale |
|---|---|---|---|
| `logDamageAssignmentOrder(prefix, assignedFor, assignedOrder, game)` | `Mage/.../game/combat/CombatGroup.java:597` (private) | DISPLAY_ONLY / UNREACHABLE_LEGACY | Dead code: zero call sites (`rg logDamageAssignmentOrder` finds only def + inner loop). Pure log formatting, no legality effect. Left untouched per "do not rename harmless symbols". |
| TODO comment "(calls some pickBlockerOrder instances ...)" | `Mage/.../game/combat/Combat.java:1020` | UNRELATED (stale comment) | No such method exists anywhere in the repo; comment describes AI `declareBlocker` behavior, not damage legality. |
| `Order of Midnight`, `Order of the Mirror`, `Silkenfist Order`, `False Orders` | `Mage.Sets` card files | UNRELATED | Card names / unrelated declare-blockers effect. |
| Mana "priority order" comment | `Mage/.../abilities/costs/mana/ManaCostsImpl.java:297` | UNRELATED | Mana payment, not combat. |
| "put them back in any order" (Gollum) | `Mage.Sets` | UNRELATED | Library ordering, not combat. |
| `BLOCKING ORDER MATTERS` comments | `Mage.Tests/.../combat/CanBlockMultipleCreaturesTest.java:41,77` | TEST_ONLY | Test-side block declaration order convenience; engine imposes no damage legality from it. |
| `blockers in any order` param doc | `Mage.Tests/.../serverside/base/impl/CardTestPlayerAPIImpl.java:460` | TEST_ONLY | Test helper doc. |
| Non-trample division (`totalMin=totalMax=damage`, per-option 0..damage) | `CombatGroup` | LEGACY_NAME_CURRENT_BEHAVIOR (free division) | Allows all-to-A, all-to-B, arbitrary split; no lethal-first ordering. Verified by 3 matrix tests. |
| Trample division (`totalMin=lethalSum`, per-option 0..damage) + WS206 per-blocker check | `CombatGroup` | CURRENT_BEHAVIOR (CR 702.19b) | Total range is a necessary but insufficient pre-filter; WS206 adds the sufficient per-blocker lethal check when through > 0. Zero-through stays free. |

## Verdict

DAMAGE_ASSIGNMENT_ORDER_PRESENT = NO. No production-reachable obsolete
(lethal-before-next / ordered-blocker) legality exists. No DAO restoration was performed;
the fix adds only the current-rule trample condition, which is order-independent
(each blocker's requirement is checked independently, never "in order").
