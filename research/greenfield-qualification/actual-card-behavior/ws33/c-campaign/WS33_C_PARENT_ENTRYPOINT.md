# WS33-C parent entrypoint demonstration (rank-1 cluster)

Source lock: `AUDIT_BASE_SHA=895240f4058076764227a418ad28e84f61d3a7ed`,
`AUDIT_BASE_TREE=cec73ae51b0168280ea648892f3e9edd46dcd883`,
`FORGE_PIN=8c7e9afb8e6caee88644b94e25da5852e36f8928` (verified at startup;
branch HEAD/TREE equal the audit lock, discrepancy NONE).

Rank-1 cluster: `forge.game.spellability.AbilitySub` /
`ws33-template-113` / `STATE_ONLY`, 176 paths. Cost shape NONE (no WS33B
Cost/payment surface). Required dimensions per path: STATE only.

## Real production parent entrypoint (pinned Forge)

File: `forge-game/src/main/java/forge/game/ability/AbilityUtils.java` at
`FORGE_PIN`:

- line 1299 `public static void resolve(final SpellAbility sa)` — the single
  production resolution entrypoint for a stack-resolving parent ability.
- `resolveApiAbility(sa, game)` (line 1377): checks conditions, calls the
  parent effect `sa.resolve()`, then unconditionally calls
  `resolveSubAbilities(sa, game)` (line ~1406).
- `resolveSubAbilities` (line 1357): reads `sa.getSubAbility()` (the
  production `AbilitySub` child linked by `AbilityFactory` from the card
  script `SubAbility$` field) and recurses into
  `resolveApiAbility(abSub, game)` (line 1374), which calls the child effect
  `abSub.resolve()`.

File: `forge-game/src/main/java/forge/game/spellability/AbilitySub.java`
at `FORGE_PIN`, line 98 `public void resolve()` → `effect.resolve(this)`.

File: `forge-game/src/main/java/forge/game/ability/AbilityFactory.java`
at `FORGE_PIN`, line ~357 `getSubAbility(state, sSub, sVarHolder)` builds
the child from the parent card-script `SubAbility$` reference; line ~88
`case SubAbility: return new AbilitySub(...)`.

So the production chain is:

```
Game stack resolves parent SpellAbility
  -> AbilityUtils.resolve(parent)               [PRODUCTION ENTRYPOINT]
    -> resolveApiAbility(parent) -> parent.resolve()      (parent effect)
    -> resolveSubAbilities(parent) -> resolveApiAbility(child)
      -> child.resolve()  (AbilitySub.resolve -> effect.resolve(child))
```

A qualification witness MUST enter at `AbilityUtils.resolve(rootParent)`
(or higher: real game trigger -> stack -> `AbilityUtils.resolve`) and
observe the child. Direct `new AbilitySub(...)` + `child.resolve()` or
direct `effect.resolve(child)` is FORBIDDEN as qualification evidence
(negative test required).

## Evidence needed to prove the target child was reached

1. **Parent provenance**: actual card identity (oracle id + card script
   path/line), parent SVar name (e.g. `TrigGainLife`), parent ApiType, root
   ability id. Source: card script at `FORGE_PIN` + runtime
   `getHostCard()` / `getApi()`.
2. **Child-reach observation**: observation-only hook in
   `AbilitySub.resolve()` (existing overlay
   `runtime-overlays/apply-ws33-svar-reachability.py`, inert unless a test
   registers an observer) capturing, for each resolved `AbilitySub`: child
   SVar identity (api + host card + parent chain via `getParent()`), and a
   monotonic sequence number proving the child resolved AFTER the parent
   effect within the same `AbilityUtils.resolve(root)` call.
3. **Exact path identity**: map
   `(parent SVar name, SubAbility$ pointer)` → `effective_v2_path_id`. For
   the pilot: parent `TrigGainLife` + pointer `DBDraw` →
   `forge-behavior-v2:b42b594f2523a243cf1b4877de9612a831bb71f6`
   (`{SubAbility: DBDraw}`, `ws33-template-113`, STATE_ONLY).
4. **Semantic postcondition**: deterministic game-state delta asserted from
   the live game object, e.g. Cloudblazer ETB: controller life +2 AND hand
   size +1 net (drew 2 after playing the card). Read from `Game`/`Player`
   objects, never injected.
5. **Decision/hidden/RNG/replay**: rank-1 cluster requires STATE only; the
   pilot card (Cloudblazer) is untargeted, choice-free, cost-free, so no
   authoritative decision tape is required. No hidden/RNG/replay evidence
   required by the canonical flags. (Draw changes hand composition; hand
   contents are not asserted, only counts + life, so no hidden payload is
   retained.)
6. **Fail-closed negative**: direct-child construction/resolution without a
   production parent must be rejected by the adjudicator
   (parent-chain == null → FAIL, not PASS).

## Pilot instantiation

Card: Cloudblazer (`forge-gui/res/cardsfolder/c/cloudblazer.txt` at
`FORGE_PIN`):
`T:Mode$ ChangesZone ... Execute$ TrigGainLife` →
`SVar:TrigGainLife:DB$ GainLife | LifeAmount$ 2 | SubAbility$ DBDraw` →
`SVar:DBDraw:DB$ Draw | Defined$ You | NumCards$ 2`.
Target C path: `forge-behavior-v2:b42b594f2523a243cf1b4877de9612a831bb71f6`.

Production drive (mirrors `Ws33SwiftwaterCliffsWitnessTest`): create game,
card to hand, `moveTo(Battlefield)`, `runWaitingTriggers()`,
`addAllTriggeredAbilitiesToStack()`, resolve stack through the production
`GameAction`/`Stack` path (which calls `AbilityUtils.resolve`), with the
`AbilitySub` observer armed. Assert trace shows parent-before-child and
life/hand deltas hold.
