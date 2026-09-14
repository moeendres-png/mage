# WS206 Validation

## Focused (new, actual-card)

- `WS206TrampleReproducerTest` 1/1 PASS (illegal 4/0+2 rejected, legal 2/2+2 executes).
- `WS206CombatDamageMatrixTest` 12/12 PASS (table in ACTUAL_CARD_MATRIX.md).

## Affected existing suites (unchanged tests, all green)

58/58 PASS in one reactor run (`-o test`, checkstyle skipped — plugin unavailable offline):

- combat DamageDistributionTest (8: incl. 2x2Block, double-strike x3, trample vs
  indestructible x2, deathtouch-trample, Phyrexian Unlife)
- combat FirstStrikeTest (all incl. gained/lost mid-combat, damage-in-between,
  prevented, zero-damage, ninjutsu)
- combat CanBlockMultipleCreaturesTest (5: incl. MultipleBlockWithTrample 1/2)
- combat CombatDamageByToughnessTest (4) + LifelinkInCombatTest
- trample prevention/two-blocker tests in the same batch
  (testOneBlockerTrample, testTwoBlockers, testTwoBlockersTrample, testDamagePrevented,
  testSomeDamagePreventedTrample, testPlayerDamagePrevented)
- keywords BandingTest (3) + DeathtouchTest (3)

## Adjacent + prior-workstream (no collateral)

18/18 PASS: TargetMultiAmountTest (8) + WS81H01CorrectedTest (3) +
WS83CR61412SystemicTest (3) + WS85FutureStateHardeningTest (4).

## Compile

- `mvn -pl Mage -o compile` (checkstyle skipped): BUILD SUCCESS (1 source file).
- Checkstyle plugin: NOT_RUN (maven-checkstyle-plugin unresolvable offline).
  No style exemption claimed; change follows surrounding file conventions.

## Review

- Changed surface: `Mage/.../game/combat/CombatGroup.java` (+160/-13) + 2 new test files.
- No weakened assertions/denominators/semantics; no card-name logic; no Lab concepts;
  no DAO restoration; no pilot-trusted legality; no secrets; diff inspected.

VALIDATION verdict: PASS (behavior), COMPILE PASS, CHECKSTYLE NOT_RUN (offline).
FULL107 = NOT_RUN. BEHAVIOR_CREDIT_CHANGE = 0. RAW_GIT_PUSH_USED = NO.
