# WS212 Final Handoff — XMage Rules-RNG Explicit Seed Authority

## Source Lock

- Repo `moeendres-png/mage`, branch `ws212/xmage-rules-rng-seed-authority-20260914`.
- Audit base = WS211 terminal `2b3f0f767b69192f90a921a9ece40abb0b8149d0`
  (tree `38a1bcada4d694959fce68bcd4908fa07e7702c9`); preserved exactly.
- WS208 reference root read-only; no Commander-Lab mutation.

## Work Completed

- XHIGH read-first adjudication of all 15 seed-lifecycle questions; classification
  `EXISTING_CORE_API_SUFFICIENT_NEEDS_TEST_HARDENING` (no production change).
- Re-verified every WS54 closure gate statically at this HEAD (0 UNKNOWN).
- Added engine qualification: `WS212RulesSeedAuthorityTest` (8/8) +
  `WS212FreshJvmProbe` (separate-JVM twins + control).
- Added game qualification: `WS212SeededRulesConsumersTest` (8/8 live games:
  twins, control, in-game shuffle, coin/die, random discard, smoothed mulligan,
  copy isolation).
- Regressions: WS54 13/13 + 7/7, WS206 13/13, WS211 20/20 (all with `-am`).
- Evidence package (this directory, 13 files) + WS213 Lab successor spec.

## New Findings

1. No production change needed: `setRulesSeed` + `requireExplicitSeed` already
   form the complete correct contract (all 15 answers + twin proof).
2. Test-harness-only deviation: unscripted `TestPlayer.flipCoinResult` /
   `rollDieResult` fall back to non-Rules `RandomUtil` (production consumes
   `game.getRulesRandom()`). Documented, not mutated; follow-up recommended.

## Changes

- New: `Mage/src/test/java/mage/WS212RulesSeedAuthorityTest.java`,
  `Mage/src/test/java/mage/WS212FreshJvmProbe.java`,
  `Mage.Tests/.../ws212/WS212SeededRulesConsumersTest.java`,
  `research/ws212-xmage-rules-rng-seed-authority/` (13 files).
- Modified: nothing in production. Zero behavior-credit change.

## Tests / Evidence

See VALIDATION.md / VALIDATION.json: 69/69 green across 6 suites
(8+13 Mage; 8+7+13+20 Mage.Tests), plus fresh-JVM twin digests.

## PASS / FAIL / UNKNOWN

- PASS: seed contract, fresh-JVM reproducibility, consumer representatives,
  accounting, copy isolation, WS206/WS211 regressions.
- UNKNOWN: `D5_TWIN_EQUALITY` (Lab-side until WS213); anything Lab-side.
- FAIL: none.

## Remaining Blockers

None in WS212 scope. Publication (push) is the only open step.

## Outputs

Evidence package + WS213 spec (this directory); three new test files.

## Dependencies Unblocked

WS213 (Lab repin/requalification) is fully specified and may proceed from the
WS212 terminal candidate.

## Exact Next Action

Publish: canonical `safe_push` dry-run, then push branch
`ws212/xmage-rules-rng-seed-authority-20260914`; verify exact remote HEAD/tree
and clean worktree; update state `validated_head`.
