# WS212 WS206 Regression (bounded, combat-damage preservation)

WS212 ships zero production diff, so the expected result is identity. Verified
with reactor-fresh artifacts (`mvn -pl Mage.Tests -am ...`,
`-Dsurefire.failIfNoSpecifiedTests=false`):

- `WS206CombatDamageMatrixTest`: 12/12 PASS.
- `WS206TrampleReproducerTest`: 1/1 PASS.

Note: an earlier run WITHOUT `-am` resolved a stale installed `mage` jar and
failed; with `-am` (correct invocation) everything is green. That failure was a
dependency-resolution artifact, never a code regression (no production files
changed in WS212).

`WS206_COMBAT_REGRESSION = PASS (13/13)`. Current-rules combat damage preserved.
