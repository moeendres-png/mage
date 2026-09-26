# RG-06B — Pre-Fix Reproducer (RED phase record)

## Coordinator checkpoint (accepted)

The branch-tip run was RED via
`RG06HiddenStateRestoreTest.restoredMorphDoesNotOfferFaceUpActivatedAbility`
failing with `Permanent not found: Akorma, Angel of Fury`. That failure is a
FIXTURE/LIFECYCLE failure (name lookup after the placeholder rename), NOT
evidence of the semantic defect. No production change was made on that basis.

## Repaired reproducer (this branch)

File: `Mage.Tests/src/test/java/org/mage/test/serverside/rg06/RG06HiddenStateRestoreTest.java`

- `restoredMorphDoesNotOfferFaceUpActivatedAbility`: pre-start
  `game.cheat` + `restoreFaceDownStateForGameLoad(MORPHED)` on Akroma, Angel
  of Fury (face-up `{R}` pump = strong discriminator), native ID captured
  pre-start, observation inside `runCode` at turn 1 PRECOMBAT_MAIN via
  `game.getPermanent(id)`.
- Non-vacuity gates (all asserted): object exists at observation point;
  `isFaceDown`; `isMorphed`; 2/2; placeholder name
  (`EmptyNames.FACE_DOWN_CREATURE`); authoritative surface
  `player.getPlayable(game, true)` scanned for source-bound pump ability.
- `naturalMorphDoesNotOfferFaceUpActivatedAbility`: negative control
  (`Akroma using Morph` face-down cast, same surface/discriminator/gates).
- `restoredMorphTurnFaceUpRestoresAbilityNormally`: positive control
  (genuine `{3}{R}{R}{R}` turn-up → 6/6 Akroma, pump offered normally).

## Outcome on UNMODIFIED baseline production code

All three GREEN. The specified defect (restored morph offers/executes the
face-up pump while natural morph does not) DOES NOT reproduce through any
faithful native path tested:

1. pre-start restore, TwoPlayerDuel — clean;
2. post-start restore in `runCode`, TwoPlayerDuel — clean (scratch probe,
   since removed);
3. post-start restore + `applyEffects` + `checkStateAndTriggered`,
   CommanderFreeForAll 4P, `getPlayable` with hidden=false AND hidden=true
   — clean (scratch probe, since removed).

The RED phase therefore did NOT yield a semantic RED. Per evidence
semantics (UNKNOWN != PASS, no fabricated failure), no defect was declared
and no production patch was authored to "turn green". See ROOT_CAUSE.md.
