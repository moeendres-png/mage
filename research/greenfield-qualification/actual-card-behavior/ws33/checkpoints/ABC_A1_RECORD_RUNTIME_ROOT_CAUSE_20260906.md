# WS33 ABC-A1 — Record runtime root cause

Date: 2026-09-06

## Boundary

Run `33996838949` is the first A1 transaction to pass exact 122/122 materialization and enter actual-card Record runtime. It produced 63 successful per-path Record markers and 59 runtime diagnostics, then failed closed before Replay and certification.

Immutable artifact:

- artifact ID `9978351349`
- digest `sha256:2658f8b854dc6a48b63d911b121e08c45cc8c4d983cab432b957c10d8ef59488`

## Diagnostic classification

All 59 diagnostics are `IllegalStateException` from the qualification harness, not engine process failures.

### Root cause A — hard-coded single-target cardinality (58 paths)

`Ws33TargetRestrictionsCampaignTest.findAbility()` rejects any actual Forge target ability unless:

```text
ability.getMinTargets() == 1
ability.getMaxTargets() == 1
```

This rejects real A1 abilities with valid optional or multi-target cardinalities before Forge can emit authoritative legal target options. Examples include `TargetMin$ 0 | TargetMax$ 1` and genuine multi-target spells/abilities.

This is a qualification-harness defect. It is not evidence of a Forge Rules Core target-legality failure.

### Root cause B — missing `TriggeredCardController` context (1 path)

`Driver of the Dead` reached the external target decision boundary but the intended graveyard creature was never emitted as an authoritative option. Its actual Forge SVar is:

```text
ValidTgts$ Creature.cmcLE2
TargetsWithDefinedController$ TriggeredCardController
```

The qualification harness currently initializes `TriggeredTarget` / `TriggeredDefendingPlayer` context but does not establish the triggering-card/controller object required by `TriggeredCardController`. This is a missing qualification context fixture, not a proven Forge target-legality defect.

## Repair contract

The repair must remain qualification-only and fail closed:

1. bind to the actual Forge min/max target cardinality instead of imposing `1/1`;
2. always select the designated intended fixture target only when Forge exposes it in authoritative legal options;
3. after selecting the intended target, select `DONE` only when Forge exposes `DONE` and the target count is legal;
4. if Forge requires more targets before `DONE`, any additional target must come from an explicitly provisioned, predeclared qualification filler set and must itself be selected by semantic identity from Forge's authoritative options — never by `first`, `default`, random, AI, or an implicit pass;
5. final assertions must require `ability.isTargetNumberValid()`, intended target retained, and actual final target count within authoritative cardinality; no hard-coded final count 1;
6. establish `TriggeredCardController` through Forge triggering-object semantics, not by bypassing TargetRestrictions;
7. no production Rules code, card scripts, coverage files, effective manifest, queue, or global registry may be changed by this repair.

Evidence classes:

- 63 success / 59 diagnostics and diagnostic messages: `DIRECTLY_VERIFIED`
- 58/1 clustering: `CODE_DERIVED` from immutable artifact diagnostics
- hard-coded `1/1` harness rejection: `CODE_DERIVED`
- `Driver of the Dead` source semantics: `DIRECTLY_VERIFIED` at pinned Forge
- repair design: `MODELED` until fresh runtime execution

`ABC_A1_RECORD_RUNTIME_ROOT_CAUSE=QUALIFICATION_HARNESS`
`ABC_A1_FORGE_RULES_CORE_FAILURE_PROVEN=FALSE`
`ABC_A1_COVERAGE_PROMOTION=FALSE`
