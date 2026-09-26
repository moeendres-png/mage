# RG-06B — Implementation

## Production changes

NONE. No file under `Mage/src/main` (or any other production source) was
modified. Verified: `git diff b1959698...HEAD -- Mage/src/main` is empty.

Rationale: the specified defect does not reproduce on the baseline through
any faithful native path (see PRE_FIX_REPRODUCER.md and ROOT_CAUSE.md), so
any production edit would be change without causation — explicitly forbidden
by the assignment hard gates.

## Test changes

`Mage.Tests/src/test/java/org/mage/test/serverside/rg06/RG06HiddenStateRestoreTest.java` only:

1. `restoredMorphDoesNotOfferFaceUpActivatedAbility`: repaired fixture
   (native-UUID observation across the placeholder rename) + hidden-info
   negatives (revealed size 0, no identity-naming offers from the source).
2. `naturalMorphDoesNotOfferFaceUpActivatedAbility` (new): negative control,
   same surface/discriminator/gates.
3. `restoredMorphTurnFaceUpRestoresAbilityNormally` (new): positive control,
   genuine `{3}{R}{R}{R}` turn-up → 6/6 + pump offered normally (restore is
   non-destructive).

Actual card throughout: Akroma, Angel of Fury (face-up `{R}` pump
discriminator). No card-name production special case (test-only vehicle).
