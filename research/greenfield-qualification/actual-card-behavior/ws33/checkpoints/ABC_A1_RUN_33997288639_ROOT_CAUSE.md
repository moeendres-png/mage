# WS33 ABC-A1 — run 33997288639 root-cause checkpoint

Date: 2026-09-06

This checkpoint follows the persisted terminal FAIL for run `33997288639`. No repair described here has yet been credited as qualification evidence.

## Root-cause partition

The 11 Record diagnostics reduce to three qualification-state families.

### RC-A — missing production target-reset initialization for divided abilities (8 paths)

Affected:

- `forge-behavior-v2:0fd90bff96b403f7de9bc94f18af5138bd8e9cb3` — Pyrotechnics
- `forge-behavior-v2:4170b515a20da1c93eeb9c41ec5ba861c93f4adb` — Kuldotha Flamefiend
- `forge-behavior-v2:54396943b719a41f8729b41070706cedae209e7f` — Fury
- `forge-behavior-v2:768292059332b0871186711dcfd29d2ef051e503` — Inferno Titan
- `forge-behavior-v2:8b15cea0e55d01a6e1599543af88c05e55d4fdda` — Fire Covenant
- `forge-behavior-v2:99b122413b19a3714084ae25a5b922a2ed617610` — Angel of Salvation
- `forge-behavior-v2:a7c010a470703ba737c4f06076a17c58f58ad3ad` — Magma Opus
- `forge-behavior-v2:acbeaf6f63df78b5bae37b910a71e60763b7b43e` — Bogardan Hellkite

The A1 harness extracts the real card-bound `SpellAbility` and calls `PlayerControllerHuman.chooseTargetsFor` directly, but does not perform Forge's target-reset initialization first.

At the pinned Forge source, `SpellAbility.clearTargets()` is not merely a list clear: when the ability is `DividedAsYouChoose`, it initializes `dividedValue` using Forge `AbilityUtils.calculateAmount(...)`. `SpellAbility.getStillToDivide()` returns zero when `dividedValue` is null. `TargetSelection.chooseTargets(...)` has a production early-success condition for divided abilities when `divisionValues == null && ability.getStillToDivide() == 0`.

Therefore the qualification harness enters target selection with an uninitialized divided amount and Forge correctly follows the state it was given without opening the intended external target decision. The observed diagnostic `authoritative intended target transition was never consumed` is a HARNESS/setup failure, not evidence of incorrect Forge target legality.

Repair requirement: invoke the same Forge target-reset initialization used by production targeting before the external target-selection boundary. Do not set a predicate result or divided outcome manually.

### RC-B — X-dependent target cardinality not established through payment state (1 path)

Affected:

- `forge-behavior-v2:435bc7ab98d86c77ead8e7302ee9e035899b7cb4` — Disorder in the Court

Pinned card source declares `ManaCost:X W U`, `TargetMin$ X`, `TargetMax$ X`, and `SVar:X:Count$xPaid`. The harness does not establish an actual paid-X state before asking Forge to select targets. Consequently the isolated target ability can evaluate to zero targets and no intended target transition is consumed.

This remains a qualification setup gap. Repair must establish X through an authentic Forge cost/payment or already-qualified production state path; the pilot/harness must not invent target cardinality or manually assert an X outcome as a Rules substitute.

### RC-C — dynamic defined-controller fixture/context handling (2 paths)

Affected:

- `forge-behavior-v2:3364d10da5cba40b6d3dce90e453e1e4abf91368` — Blue Mage's Cane
- `forge-behavior-v2:c03e4fcca787870139089ee48c6be35575e3e733` — Driver of the Dead

Pinned Blue Mage's Cane source uses `TargetMin$ 0 | TargetMax$ 1 | ValidTgts$ Instant,Sorcery | TargetsWithDefinedController$ TriggeredDefendingPlayer | Origin$ Graveyard`. Current fixture logic keys `TriggeredDefendingPlayer` setup from the `ValidTgts` text in one path, so this parameter-only use does not receive the required defending-player triggering context.

Pinned Driver of the Dead source uses `ValidTgts$ Creature.cmcLE2 | TargetsWithDefinedController$ TriggeredCardController | Origin$ Graveyard`. The run's materialized case designates `OPPONENT_CREATURE`, while the repair sets `AbilityKey.Card` to the actor-controlled source. That is internally inconsistent with the authoritative defined-controller restriction. The fixture role must be derived from the actual Forge defined-controller context rather than the selector string alone.

Repair requirement: derive dynamic controller context from actual ability parameters and establish real triggering/defending objects. Provision the intended target in the corresponding real zone/controller/owner state. Forge must still emit the legal option; the harness may never reinterpret `ValidTgts` as legality.

## Classification

- terminal counts and affected IDs: `DIRECTLY_VERIFIED` from immutable artifact `9978478230`
- pinned `SpellAbility.clearTargets()` / `TargetSelection` initialization behavior: `DIRECTLY_VERIFIED` / `CODE_DERIVED` from Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Disorder in the Court / Blue Mage's Cane / Driver of the Dead card-script parameters: `DIRECTLY_VERIFIED` from the same Forge pin
- repair design: `MODELED` until a fresh immutable run proves it

`ABC_A1_ROOT_CAUSE_CLASS=HARNESS_FIXTURE`
`ABC_A1_FORGE_RULES_CORE_FAILURE_PROVEN=FALSE`
`ABC_A1_COVERAGE_PROMOTION=FALSE`
