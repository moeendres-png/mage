# RG-08 — General Replacement-Effect Timing Qualification

## Final Handoff — 2026-09-25

**Disposition:** `RG08 = QUALIFICATION_CLOSURE_NO_PRODUCTION_CHANGE`

**Architecture Freeze:** `NOT CLAIMED`

**Production Provider:** `NOT SELECTED`

**WORKTREE:** `NOT_AVAILABLE_IN_CONNECTOR_EXECUTION`

## Source Lock

- Repository: `moeendres-png/mage`
- Exact RG-07 source base: `83bd96b195dc9757e86597d7d4afaaa8066a9527`
- Workstream branch: `sol/rg08-replacement-regressions-20260924`
- Runtime-verified source head: `602bc3ae70c5c443ce0ddf90202d4a6ddf7d9535`
- Runtime-verified tree: `d4e13be550361d5e9aac75eda55c3f70dd36d1ef`
- Draft CI PR: #15. CI-only; DO NOT MERGE TO Mage master.

## Reuse / Adjudication

`ENGINE_NATIVE_REUSE`

The current `ContinuousEffects.replaceEvent` mechanism was qualified test-first. No direct systemic replacement-engine defect was reproduced, therefore no production rewrite was authorized.

The existing engine path:

1. recomputes applicable replacement effects after each non-terminal application;
2. removes already-consumed effect/ability pairs;
3. records applied replacement effect IDs on the event;
4. lets the affected player select when multiple effects are applicable;
5. stops when an event is completely replaced;
6. otherwise continues with the modified event;
7. preserves dedicated Commander replacement behavior;
8. retains the prior WS83/WS85 CR 614.12 future-state applicability hardening.

## Rules Authority

Current official Magic Comprehensive Rules from Wizards were reverified during closure. The applicable authority remains the current rules for replacement effects (CR 614) and interaction/ordering of replacement and prevention effects (CR 616). Engine behavior is evidence, not Rules authority.

## Work Completed

1. Bound RG-08 directly to terminal `RG07_MAGE_HEAD`.
2. Inspected exact `ContinuousEffects.replaceEvent`, replacement-effect discovery, consumed/application tracking and affected-player choice path.
3. Inspected and reused WS83 / WS85 CR 614.12 future-state regressions.
4. Inspected current actual-card replacement corpus including Doubling Season, Pir, Academy Manufactor, Dredge, Rest in Peace and prevention interactions.
5. Added seven bounded actual-card-driven RG-08 tests.
6. Executed the exact RG-08 source head through repository CI.
7. Re-ran inherited RG-02, RG-07, WS83 and WS85 evidence in the same cumulative runtime.
8. Found no direct systemic replacement-engine defect.
9. Made no production Rules-Core change.

## Production Changes

**NONE.**

## Test Changes

Added:

`Mage.Tests/src/test/java/org/mage/test/serverside/rg08/RG08ReplacementTimingTest.java`

Runtime-qualified methods:

1. `optionalDredgeDeclinedDoesNotLoopAndNormalDrawContinues`
2. `affectedControllerCanChooseSeasonBeforePir`
3. `affectedControllerCanChoosePirBeforeSeasonAndApplicabilityRecomputes`
4. `sameReplacementDoesNotApplyTwiceToSameEvent`
5. `damageReplacementThenPreventionUsesModifiedDamageEvent`
6. `multiObjectDestroyConsumesZoneReplacementForEachObject`
7. `dredgeReplacementFeedsModifiedContinuationNotStaleDraw`

## Required Matrix Adjudication

### 1. Optional replacement offered and declined; no loop

PASS — actual-card Stinkweed Imp Dredge is declined. The normal draw proceeds exactly once and the Dredge replacement does not loop.

### 2. Multiple applicable replacements; affected player chooses ordering

PASS — actual-card Doubling Season + Pir, Imaginative Rascal + Chandra, Fire Artisan.

Both orderings were explicitly selected and produced their distinct expected results.

### 3. Modified event causes applicability recomputation

PASS — Pir-first makes the subsequent Doubling Season application relevant to the modified counter event. Existing Academy Manufactor multiple-replacement coverage also executed green in the same run.

### 4. Same replacement cannot illegally replace the same event repeatedly

PASS — one Doubling Season produces exactly two spore counters from a single Pallid Mycoderm counter event, not recursive repeated doubling. Code-derived evidence additionally shows applied-effect and consumed-effect tracking.

### 5. Replacement followed by prevention

PASS — actual Furnace of Rath + Test of Faith + Shock scenario. Modified damage is consumed by the normal prevention path and produces the expected surviving creature/counters/damage state.

The inherited `DoublingSeasonTest.test_Counters_ByPreventEffect` also executed green.

### 6. Multi-object / batch event

PASS — Rest in Peace + Wrath of God moves both destroyed creatures to exile, independently and correctly, with no stale graveyard result.

The inherited Academy Manufactor multi-replacement/token tests also executed green.

### 7. Continuation consumes modified result, not stale pre-replacement data

PASS — accepting Stinkweed Imp Dredge replaces the draw: the Imp returns to hand, five library cards move to graveyard, and the original top card is not also drawn.

### 8. State mutation during replacement discovery/application must not corrupt iteration

PASS via inherited, runtime-reexecuted WS85 coverage:

- `testP0_SentinelControl_NormalCopyUnaffected`
- `testP1_HumilityFirst_ProbeMustNotExposeEnteringOrMutateLive`
- `testP2_HumilityFirst_UnrelatedLiveStateUnchanged`
- `testF1_ProbeFailureMustSurfaceExplicitly_NoSilentAllow`

These bind actual Clone/Humility behavior to explicit purity and fail-closed future-state probes.

### 9. Multiplayer / APNAP or affected-player ordering where required

For the replacement path under qualification, the relevant CR 616 decision is affected-object/controller or affected-player ordering rather than generic APNAP stack ordering. That authoritative choice boundary is exercised by the Season/Pir and damage replacement/prevention cases.

No separate APNAP production repair was implicated.

### 10. Actual-card-driven cases

PASS. The selected systemic mechanisms are exercised through real cards; test-only sentinels in WS85 observe purity/failure semantics but do not substitute for the actual Clone/Humility behavior.

## Existing Regressions Re-executed on the Exact RG-08 Head

### WS83

All green:

- `testCloneDressDownFirst_NoCopyDecision`
- `testVesuvaHumilityFirst_CopyPreserved`
- `testPhantasmalImageHumilityFirst_NoCopyDecision_DiesAfterHumilityLeaves`

### WS85

All green:

- `testP0_SentinelControl_NormalCopyUnaffected`
- `testP1_HumilityFirst_ProbeMustNotExposeEnteringOrMutateLive`
- `testF1_ProbeFailureMustSurfaceExplicitly_NoSilentAllow`
- `testP2_HumilityFirst_UnrelatedLiveStateUnchanged`

### Other actual-card replacement corpus

The same full Mage Tests run also reports green for:

- all `DoublingSeasonTest` cases, including both Season/Pir ordering cases and replacement/prevention;
- all `AcademyManufactorTest` cases, including multiple replacement effects;
- the full inherited RG-07 Hex regression matrix;
- the full inherited RG-02 Commander-damage matrix.

## Runtime Evidence

GitHub Actions run: `36067185582`

Job: `107859567540`

Exact source head: `602bc3ae70c5c443ce0ddf90202d4a6ddf7d9535`

Exact tree: `d4e13be550361d5e9aac75eda55c3f70dd36d1ef`

`Mage Tests 1.4.61`:

- tests run: `6919`
- failures: `0`
- errors: `0`
- skipped: `125`
- module result: `SUCCESS`

All seven new RG-08 tests were individually reported `[OK]`.

### Whole-Reactor Result

The top-level reactor later failed only in the independent `Mage.Verify` module:

- 15 card-data subtype verification errors;
- one missing set implementation.

Classification:

`FULL_MAVEN_REACTOR = FAIL_AMBIENT_MAGE_VERIFY`

This ambient repository-maintenance failure is not converted into green CI, but it does not invalidate the successful Mage Tests module or RG-08 runtime semantics.

## Evidence Classification

- RG-07 -> RG-08 ancestry: `DIRECTLY_VERIFIED`
- exact runtime checkout/source tree: `DIRECTLY_VERIFIED`
- `ContinuousEffects.replaceEvent` structure: `CODE_DERIVED`
- seven RG-08 actual-card tests: `DIRECTLY_VERIFIED` + `TECHNICALLY_CONFORMANT`
- inherited WS83/WS85 execution: `DIRECTLY_VERIFIED`
- inherited Academy Manufactor / Doubling Season execution: `DIRECTLY_VERIFIED`
- official replacement/prevention semantics: `EXTERNALLY_RULE_VALIDATED`

## PASS / FAIL / UNKNOWN

### PASS

`RG08_GENERAL_REPLACEMENT_EFFECT_TIMING = PASS`

`RG08 = QUALIFICATION_CLOSURE_NO_PRODUCTION_CHANGE`

### FAIL

`FULL_MAVEN_REACTOR = FAIL_AMBIENT_MAGE_VERIFY`

### UNKNOWN

No required RG-08 semantic cell remains UNKNOWN.

## Production Engine Semantics Changed

`NO`

## Prior Evidence Impact

- RG-02 Commander-damage evidence: retained and re-executed green.
- RG-07 target-offering evidence: retained and re-executed green.
- WS83/WS85 future-state replacement evidence: retained and re-executed green.

No production source changed in RG-08, so no semantic invalidation occurred.

## Remaining Blockers

None inside RG-08.

## Dependencies Unblocked

RG-06A may start from the exact terminal RG-08 handoff commit.

## Exact Next Action

Create/resume `sol/rg06-hidden-state-restore-20260924` from the exact terminal `RG08_MAGE_HEAD`. Do not restart from Mage master and do not merge RG-08 to master.
