# WS16 — Trigger / Replacement / Zone / SBA Witnesses — Handoff

WORKSTREAM_COMPLETE: `TRUE`

BRANCH: `work/ws16-witness-trigger-zone-sba-20260829`

BASE_SHA: `d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5`  
BASE_TREE: `5725f47951938bc71af181cf1617e6b3be158804`

FORGE_PIN: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Qualified engine witness

The actual pinned-Forge semantic test was executed at:

- QUALIFIED_IMPLEMENTATION_HEAD: `b6927c63f2dfcbc45b6357351be2828917db1a2c`
- QUALIFIED_IMPLEMENTATION_TREE: `17c90ee714d5b2512df1c1fe2872b7c236fe0078`
- EXECUTION_RUN_ID: `33270636779`
- EXECUTION_JOB_ID: `99148367194`
- EXECUTION_ARTIFACT_ID: `9720024348`
- EXECUTION_ARTIFACT_DIGEST: `sha256:9d231f95ca45b84f170a3b7eb370a7f4aef821f7a06807840f0cb95ad41e0fd7`
- artifact: `ws16-pinned-forge-execution`

The Forge execution step and immutable execution-artifact upload both succeeded. The overall original job was red only because its later artifact-identity packaging step failed; that later failure does not invalidate the already-uploaded engine evidence.

The semantic witness exercises the real pinned Jwar Isle Refuge script without changing Forge implementation. It proves the systemic Forge lifecycle:

1. the `Moved` replacement causes the land to enter tapped;
2. the zone-change trigger is queued without resolving during movement;
3. `TriggerHandler.runWaitingTriggers()` produces a simultaneous trigger stack entry;
4. `MagicStack.addAllTriggeredAbilitiesToStack()` moves that entry onto the regular stack through the normal SBA/priority boundary;
5. normal priority/stack processing resolves the trigger;
6. controller life changes by exactly `+1` and the stack becomes empty.

The harness was corrected after direct source inspection of the exact Forge pin. No expected value was changed to match a bad result, no card-name production exception was introduced, and no direct ability-resolution bypass replaced the normal stack path.

## Recovery/materialization evidence

The already-successful engine artifact above was recovered without re-running Forge and materialized through the WS14 witness ABI at:

- RECOVERY_SOURCE_HEAD: `2fc51cb355423bae73647e076bf204a0a10eb406`
- RECOVERY_SOURCE_TREE: `13f56fcc942a3534765a2a921be19ef994a7178b`
- RECOVERY_RUN_ID: `33272938913`
- RECOVERY_JOB_ID: `99154590943`
- RECOVERY_ARTIFACT_ID: `9720648943`
- RECOVERY_ARTIFACT_DIGEST: `sha256:10457ba3256fe00948876903883cc0df07084b1ab60226c4a9eb10118953dc97`
- artifact: `ws16-trigger-replacement-zone-sba-witness-shard`

The recovery workflow independently rechecked the exact WS14 base/tree and primitive-manifest digest, exact tested source HEAD/tree, original engine run/job/artifact/digest, exact Forge head embedded in the execution artifact, execution-file SHA-256 checks, WS14 witness schema/semantic validation, and primitive uniqueness.

## Primitive result

WS14 assigns `53` primitives to `TRIGGER_REPLACEMENT_ZONE_SBA`:

| Status | Count |
|---|---:|
| PASS | 2 |
| PARTIAL | 51 |
| UNKNOWN | 0 |
| UNSUPPORTED | 0 |

The only promoted primitive IDs are:

- `forge-primitive-v1:affff0f8993d9b11ad9f1fb7cae35907` — actual `Moved` replacement path
- `forge-primitive-v1:5f99c3f437013e47c874b90e66bc3074` — actual `ChangesZone` trigger path through queued/simultaneous/regular stack and resolution

Every other WS16-owned primitive remains `PARTIAL` because no exact pinned-Forge actual-card state witness was executed for that primitive. Shared implementation similarity is not used as semantic proof.

Q6_ACTUAL_CARD_BEHAVIOR: `NOT_ADJUDICATED`

## Evidence classification

- pinned Forge source/lifecycle derivation: `CODE_DERIVED`
- actual engine execution and state assertions: `TECHNICALLY_CONFORMANT`
- replacement/trigger semantic adjudication against current Magic rules: `EXTERNALLY_RULE_VALIDATED`
- 51 unexecuted exact primitives: `UNKNOWN` evidence, represented as `PARTIAL` coverage rows

## Integration contract

WS24 may consume this branch and the two immutable artifacts above read-only. It must preserve the exact two PASS primitive identities, retain all 51 remaining primitives as non-PASS unless new actual execution evidence exists, and must not infer Q6 PASS from this workstream alone.
