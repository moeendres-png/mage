# RG-06B — Test Matrix (all on exact baseline production code)

## A. Direct defect + controls (RG06HiddenStateRestoreTest)

- `restoredMorphDoesNotOfferFaceUpActivatedAbility` — PASS ([OK]).
- `naturalMorphDoesNotOfferFaceUpActivatedAbility` — PASS ([OK]).
- `restoredMorphTurnFaceUpRestoresAbilityNormally` — PASS ([OK]).

## B. RG-06A regression (same class, unmodified tests)

All 10 inherited tests PASS: exact library order, later draw,
search/shuffle, invalid payloads, Sagu morph + turn-up, manifest/cloak
distinctness, disguise ward/trigger, zone-change new-object, invalid
face-down fail-closed. Class total: 13/13.

## C. Face-down engine regression (actual-card suites)

- `MorphTest, MegamorphTest, ManifestTest`: 72/72 PASS.
- `DisguiseTest`: 3/3 PASS.

## D. Cumulative residual lineage (post-change rerun; no production change,
   recorded for impact adjudication)

- RG-02 (`RG02CommanderDamageRestoreTest/4P/5P`): all PASS.
- RG-07 (`RG07HexPlayableBaselineTest`): all PASS.
- RG-08 (`RG08ReplacementTimingTest`): all PASS.
- Combined run: 29/29 PASS.

## E. Hidden-information negatives

Covered in A: revealed-size-zero + no identity-naming offers while face
down. RG-06A `assert face-down restore does not reveal identity` also green.
