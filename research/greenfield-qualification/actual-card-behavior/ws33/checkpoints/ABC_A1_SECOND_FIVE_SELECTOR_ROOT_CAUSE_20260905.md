# WS33 ABC-A1 — second five-selector root cause

Date: 2026-09-05

## Boundary

Source branch before repair: `work/ws33-g3-final-closure-20260902`
Pre-repair HEAD: `e22c6d1529e11cf3b1fafe64c689fef87e104a5e`
Run establishing the omission set: `33938471426`
Artifact: `9961000389`
Artifact digest: `sha256:cf00923211a5c78f1f5c8c3e83ba85bd2800996a1ccf7cd23479ac82cc4510bc`

No coverage promotion is authorized by this checkpoint.

## Directly verified omitted paths

The immutable 4188 successor manifest binds the five omitted IDs to these actual Forge source selectors:

1. `forge-behavior-v2:12c6c4325fb92fcd0f5d2bbe07c2679152c89f9c`
   - `lorehold_charm.txt`
   - `Artifact.cmcLE2+YouOwn,Creature.cmcLE2+YouOwn`
   - Graveyard target.
2. `forge-behavior-v2:16ac36d0e2b4715a787864d587400f91e314e801`
   - `wash_away.txt`
   - `Card.!wasCastFromTheirHand`
   - Spell target.
3. `forge-behavior-v2:2085b827a5d49d535a3d2b5ca17d4cc9c66c25c0`
   - `air_servant.txt`
   - `Creature.withFlying`.
4. `forge-behavior-v2:236471fd27480662959ef51e07f1fb84c21f4795`
   - `hidden_hideout.txt`
   - `Creature.YouCtrl+HasCounters`.
5. `forge-behavior-v2:27cf9487a495125599341a3c8b3d6a0f6aaa29ce`
   - `fiendish_panda.txt`
   - `Creature.cmcLEX+YouOwn+nonBear+Other`
   - Graveyard target.

## Forge-source adjudication

Pinned Forge `CardProperty` evaluates keyword selectors through the card's actual keyword state, counter selectors through actual card counter state, CMC comparisons through `Card.getCMC()` plus `AbilityUtils.calculateAmount`, and `wasCastFrom...` selectors from the card's actual cast-origin state. `GameActionUtil`/stack code preserves `castFrom` when a spell object is moved/admitted to the stack. Forge exposes actual counter mutation through `Card.addCounterInternal(...)` / `CounterEnumType`.

Therefore this is a qualification-fixture coverage gap, not an established Rules Core defect. The correct repair is to extend only the qualification fixture catalog/test with real Forge state:

- owned CMC<=2 graveyard artifact fixture;
- spell moved to stack from a non-hand zone;
- actual Flying creature fixture;
- owned creature with an actual +1/+1 counter;
- owned zero-CMC non-Bear creature graveyard fixture.

Forge remains the sole legality authority: a fixture is selectable only if `PlayerControllerHuman.chooseTargetsFor` emits its semantic option in the authoritative legal request. No direct `effect.resolve`, no card-name production branch, no pilot fallback, no Rules Core mutation.

## Classification

- omitted path/source bindings: `DIRECTLY_VERIFIED`
- selector-state behavior: `CODE_DERIVED`
- root cause: `QUALIFICATION_FIXTURE_CATALOG_GAP`
- Forge Rules Core defect: `NOT_ESTABLISHED`
- coverage promotion: `FALSE`

`ABC_A1_SECOND_FIVE_ROOT_CAUSE=QUALIFICATION_FIXTURE_CATALOG_GAP`
`ABC_A1_COVERAGE_PROMOTION=FALSE`
