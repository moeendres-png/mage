# RG-07 — Exact-N Target Legal-Action Offering

## Final Handoff — 2026-09-25

**Disposition:** `RG07 = PASS` / `QUALIFICATION_CLOSURE_NO_PRODUCTION_CHANGE`

**Architecture Freeze:** `NOT CLAIMED`

**Production Provider:** `NOT SELECTED`

**WORKTREE:** `NOT_AVAILABLE_IN_CONNECTOR_EXECUTION`

## Source Lock

- Implementation repository: `moeendres-png/mage`
- Exact source base from RG-02: `9c0b264f8a0688814e094076243278db5f2b08a7`
- Workstream branch: `sol/rg07-exact-n-target-offer-20260924`
- Runtime-verified source head: `f4fd8a823e39d88be88f8995e99dd35231749663`
- Runtime-verified tree: `f0e37b96713fb926d06455374c18d75f9ac94d16`
- Current pre-handoff head: `7ba0d284573daf230e0354c720c19185ed429184`
- Current pre-handoff tree: `f0e37b96713fb926d06455374c18d75f9ac94d16`
- The current pre-handoff tree is byte-identical to the runtime-verified tree.
- Draft CI PR: #14. It is a CI-only vehicle and MUST NOT be merged to Mage master.

## Baseline Reproduction Adjudication

The previously observed condition "Hex is not offered by Player.getPlayable despite six legal creatures and sufficient mana" **does not reproduce on the RG-02 lineage**.

The initial three actual-card baseline tests executed:

- 5 legal creatures -> Hex NOT offered — PASS
- exactly 6 legal creatures -> Hex offered — PASS
- 7 legal creatures -> Hex offered — PASS

The assignment explicitly allowed the already-fixed path. The superseding generic implementation is present in the source base rather than being introduced by RG-07.

## Superseding Generic Implementation

Reuse classification: `ENGINE_NATIVE_REUSE`.

Current legal offering follows the native path:

`PlayerImpl.getPlayable`
-> `getPlayableFromObject...`
-> `findActivatedAbilityFromPlayable`
-> `canPlay`
-> `SpellAbility.canActivate`
-> `AbilityImpl.canChooseTarget`
-> `Target.canChooseFromPossibleTargets`.

The generic target predicate computes:

- already selected target count;
- remaining legal possible targets;
- minimum target cardinality;
- maximum target cardinality.

It rejects an exact-N action if the remaining legal pool cannot satisfy the minimum.

Relevant historical generic targeting remediation on the inherited lineage includes:

- `c7a485b7284b1b6a8fd0fad693433f5b0f383876` — shared possible-target targeting refactor and multi-target support;
- `133e4fe4256a561d22052dd5240f4f445ed3d30b` — target-selection rework including impossible-target and multi-target cases;
- `2833460e593bd4cf61aba8bb8a5ef4d1c07ed75b` — target-option performance/stability follow-up.

RG-07 does not claim which historical commit alone fixed the formerly observed Hex symptom; it proves that the current authoritative lineage contains the generic corrected behavior.

## Work Completed

1. Bound RG-07 directly to terminal `RG02_MAGE_HEAD`.
2. Added an actual-card Hex baseline before any production remediation.
3. Executed the baseline and proved the historic defect is already absent.
4. Inspected the full legal-offer path through PlayerImpl, SpellAbility, AbilityImpl and Target.
5. Reviewed relevant target-system history.
6. Added and executed bounded actual-card/generic regressions for exact-N, up-to-N, zero-target, hexproof-reduced target pools, stale/illegal target resolution, and cost-reduced offering/casting agreement.
7. Verified real Hex casting chooses exactly six targets and with seven legal creatures leaves the seventh untouched.
8. Performed independent exact-cardinality sanity check: C(5,6)=0, C(6,6)=1, C(7,6)=7.
9. Did not add any production card-name special case or Lab/provider fabricated action.

## Production Changes

**NONE.**

No production Rules-Core or card implementation file changed.

## Test Changes

`Mage.Tests/src/test/java/org/mage/test/serverside/rg07/RG07HexPlayableBaselineTest.java`

Nine runtime cases:

1. `hexNotOfferedWithFiveLegalCreatures`
2. `hexOfferedWithExactlySixLegalCreatures`
3. `hexOfferedWithSevenLegalCreatures`
4. `hexActualCastSelectsExactlySixTargets`
5. `hexWithSevenTargetsCastsWithExactlySixAndLeavesSeventh`
6. `hexproofReducesLegalPoolBelowSixSoHexIsNotOffered`
7. `oneTargetBecomingIllegalAfterOfferingDoesNotCorruptResolution`
8. `costReductionGetPlayableAgreesWithActualHexCast`
9. `genericTargetCardinalitySemanticsRemainConsistent`

The generic cardinality case covers exact-two rejection with only one legal target, up-to-two legality, and min=max=0 zero-target semantics.

Alternative casting characteristics were not implicated by a reproduced defect or production repair in RG-07; therefore the prompt's conditional alternative-characteristics regression was adjudicated N/A rather than broadening into an unrelated casting campaign.

## Runtime Evidence

GitHub Actions run: `36065707336`

Job: `107855059768`

Exact tested head: `f4fd8a823e39d88be88f8995e99dd35231749663`

The inherited RG-02 workflow binding caused CI to checkout the exact PR head, not a synthetic merge ref.

`Mage Tests 1.4.61`:

- tests run: `6912`
- failures: `0`
- errors: `0`
- skipped: `125`
- module result: `SUCCESS`

All nine RG-07 methods were individually reported `[OK]`.

### Whole-Reactor Result

The reactor later failed in the independent `Mage.Verify` module with the already-observed ambient card-data drift:

- 15 card subtype verification errors;
- one missing set implementation.

This is not relabeled as green whole-reactor CI.

## Evidence Classification

- RG-02 -> RG-07 ancestry: `DIRECTLY_VERIFIED`
- exact current/runtime tree equality: `DIRECTLY_VERIFIED`
- target-path structure and historical implementation lineage: `CODE_DERIVED`
- Hex 5/6/7 offering: `DIRECTLY_VERIFIED` + `TECHNICALLY_CONFORMANT`
- actual Hex cast with exactly six targets: `DIRECTLY_VERIFIED` + `TECHNICALLY_CONFORMANT`
- hexproof target-pool reduction: `DIRECTLY_VERIFIED`
- target becoming illegal after offering: `DIRECTLY_VERIFIED`
- cost-reduction offer/cast agreement: `DIRECTLY_VERIFIED`
- exact/up-to/zero cardinality abstraction: `DIRECTLY_VERIFIED`
- Wolfram finite combinatorial sanity check: `MODELED`, supplemental only.

## PASS / FAIL / UNKNOWN

### PASS

`RG07_EXACT_N_TARGET_LEGAL_ACTION_OFFERING = PASS`

### FAIL

`FULL_MAVEN_REACTOR = FAIL_AMBIENT_MAGE_VERIFY`

### UNKNOWN

No required RG-07 semantic cell remains UNKNOWN.

## Production Engine Semantics Changed

`NO`

## Remaining Blockers

None inside RG-07.

## M1 Impact Adjudication

RG-07 made no production engine changes. RG-02 Commander-damage runtime evidence remains valid.

## Dependencies Unblocked

RG-08 may start from the terminal RG-07 head after this handoff commit.

## Exact Next Action

Create/resume `sol/rg08-replacement-regressions-20260924` from the exact terminal RG07 head. Do not restart from Mage master and do not merge RG-07 to master.
