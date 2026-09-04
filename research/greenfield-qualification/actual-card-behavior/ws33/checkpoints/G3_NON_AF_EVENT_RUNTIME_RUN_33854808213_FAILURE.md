# WS33 G3 non-AF event runtime — run 33854808213 terminal failure

Classification: DIRECTLY_VERIFIED / CODE_DERIVED

Canonical branch before checkpoint:

- HEAD: `f425015ae3e65afb8e2e7f7bd10ce3ab4b2cb1a6`
- TREE: `d7d855eaafa272bb95f16f6789d1e61023d74436`

Qualification source and immutable evidence:

- SOURCE_HEAD: `99377107cf860876bd5ee43fbc8121802ad9336e`
- SOURCE_TREE: `515c9847f54fd4eeb1a3375a36913a6cc990d274`
- RUN: `33854808213`
- JOB: `100965530844`
- ARTIFACT: `9929834690`
- DIGEST: `sha256:86c85663680643b6fba00ebc0450df15d9d192b6d8d36f13f74ed494b9a51d82`
- local ZIP SHA-256 independently matches the GitHub digest exactly.

## Workflow result

- source/topology/pin/overlay/harness gates: PASS
- Step 14 33-parent record campaign: PASS
- Step 15 strict adjudication: FAIL
- replay/source-chain: correctly skipped
- artifact upload: PASS

## Material progression

The two directly proven generic event-fixture repairs are confirmed:

- all five previously failing `Phase` parents now pass;
- both previously failing `AttackersDeclared` parents now pass;
- no new parent regression appears.

Strict record partition is now:

- parent entrypoints: `32 PASS / 1 FAIL` of 33
- effective paths: `31 PASS / 1 FAIL` of 32

No partial PASS is promoted.

## Sole remaining runtime blocker

`forge-behavior-v2:ae82d4423a23aaf18b7da0e9215165e8d55ba5f2#1`

- card: `Study Hall`
- source directive: `SVAR`
- parent SVar: `TrigSpent`
- mode: `SpellCast`
- target SVar: `TrigScry`
- target dispatch: `Scry`
- admission/binding/execution: `0/0/0`
- failure: `source-proven trigger admission count=0`

The target is not entered directly. The harness creates the delayed trigger through the actual source mana ability's `AbilityManaPart.addTriggersWhenSpent(spell)` and then admits the commander spell through `MagicStack.addAndUnfreeze(spell)`.

Pinned Forge facts already verified:

- `AbilityManaPart.addTriggersWhenSpent` parses `TrigSpent`, remembers the spell being paid, sets the spawning ability when available, and registers a this-turn delayed trigger.
- `MagicStack.add` emits `SpellCast` with `holdTrigger=true` after stack admission and `applyPayingManaEffects()`.
- `MagicStack.unfreezeStack` resets active triggers and runs waiting triggers.
- `TriggerSpellAbilityCastOrCopy.performTest` checks `ValidActivatingPlayer`, `ValidCard`, `ValidSA`, and for a spawning ability with `TriggersWhenSpent`, requires the trigger-remembered set to contain the exact spell ability.

The current evidence does not identify which of those gates rejects Study Hall. Therefore the root cause remains `UNKNOWN`; no Study-Hall-specific repair is authorized.

## Next authorized action

Add observation-only trigger-gate telemetry around pinned `TriggerHandler.canRunTrigger` / the generated Study-Hall delayed trigger. It must record the exact rejection stage without changing the boolean result, legal options, state, RNG, stack order, trigger identity, or pilot behavior. The next successor may be diagnostic-first; any repair must be separately checkpointed after the rejection stage is directly established.

## State

- `G3_NON_AF_STATUS = UNKNOWN`
- `COVERAGE_PROMOTION = FALSE`
- G3 remains open
- ABC/D/E/F remain serially blocked
