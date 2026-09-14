# WS206 Actual-Card Matrix (all native engine, strict choose mode)

File: `Mage.Tests/.../ws206/WS206CombatDamageMatrixTest.java` (12 tests) plus
`WS206TrampleReproducerTest.java` (reject-then-accept). Result: 13/13 PASS.

| # | Category | Cards | Attempt | Expectation | Result |
|---|---|---|---|---|---|
| 1 | Non-trample all-to-A (510.1c) | Alpine Grizzly 4/2 vs Bears 2/2 + Lion 2/2 | 4,0 | Bears dies, Lion 0, life 20 | PASS |
| 2 | Non-trample all-to-B | same | 0,4 | Bears 0, Lion dies, life 20 | PASS |
| 3 | Non-trample split | same | 1,3 | Bears 1 lives, Lion dies, life 20 | PASS |
| 4 | Trample lethal+through | Dreadmaw 6/6T vs Bears+Lion | 2,2 (+2) | both die, life 18 | PASS |
| 5 | Trample zero-through free (below lethal OK) | same | 6,0 (+0) | Bears dies, Lion 0 lives, life 20 | PASS |
| 6 | Illegal through rejected then legal | Dreadmaw vs Bears+Lion | 4,0 rejected; 2,2 accepted | both die, life 18 | PASS (reproducer) |
| 7 | Already-marked | Dreadmaw vs Crab 1/6 (4 marked via 2x Shock) + Bears | 2,2 (+2) | both die, life 18 | PASS |
| 8 | Protection (no lowering) | Dreadmaw (green) vs Lynx 2/1 prot-green + Bears | 0,3 rejected; 1,2 accepted (+3) | Lynx 0-actual lives, Bears dies, life 17 | PASS |
| 9 | Deathtouch+trample | Dreadmaw + Bladebrand vs Bears+Lion | 1,1 (+4) | both die, life 16 | PASS |
| 10 | First strike scoped | White Knight 2/2 FS vs Bears+Lion | 2,0 (FS step) | Bears dies FS; Lion kills Knight normal; life 20 | PASS |
| 11 | Double strike both steps | Warren Instigator 1/1 DS vs Bears+Lion | 1,0 then 1,0 | Bears dies, Lion 0, life 20 | PASS |
| 12 | Banding controller (702.22j) | Dreadmaw vs Infantry 1/3 banding + Bears | defender chooses 3,2 (+1) | both die, life 19 | PASS |
| 13 | Blocker vs attackers (510.1d) | Crab 1/6 + Brave the Sands vs Bears + Lion | Crab 1,0 | Bears 1, Lion 0, Crab 4 lives, life 20 | PASS |

Prevention note: prevention-effect lethal semantics share the protection code path
(`getLethalDamage` ignores both); covered by the protection matrix case plus the
pre-existing `firstStrikeDamagePrevented` regression (PASS in the 58-test batch).
Wither/infect deferred-counter visibility across shared blockers is a documented
approximation (see ARCHITECTURE_ADJUDICATION 7); no matrix case hides it.

ACTUAL_CARD_BEHAVIOR = PASS (13/13, all actual cards; no synthetic-only credit).
CR510_1C_FREE_DISTRIBUTION = PASS. CR510_1D_MULTI_ATTACKER_BLOCKER_DISTRIBUTION = PASS.
CR510_1E_COMPLETE_ASSIGNMENT_VALIDATION = PASS. DAMAGE_ALREADY_MARKED = PASS.
SIMULTANEOUS_ASSIGNMENT_ACCOUNTING = PASS (common case) / APPROXIMATION (prevented/
wither-shared narrow case, documented). DEATHTOUCH_TRAMPLE = PASS.
PROTECTION_PREVENTION_LETHAL = PASS. BANDING_ASSIGNMENT_CONTROLLER = PASS.
FIRST_STRIKE = PASS. DOUBLE_STRIKE = PASS. PLAYER_MULTI_AMOUNT_SEAM = PRESERVED.
