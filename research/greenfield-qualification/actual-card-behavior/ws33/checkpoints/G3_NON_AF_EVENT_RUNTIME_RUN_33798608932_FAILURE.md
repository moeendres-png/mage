# G3 NON-AF EVENT RUNTIME — RUN 33798608932 FAILURE

Evidence classification: `DIRECTLY_VERIFIED`.

## Immutable run identity

```ini
EVIDENCE=DIRECTLY_VERIFIED
RUN=33798608932
JOB=100792262743
SOURCE_HEAD=26ec46d852a731054e8719e5bf1ea37bef3f6ea6
SOURCE_TREE=793c1e3c10cf07f4d0b432a56aa0f90e73eb7fe0
ARTIFACT=9910414457
ARTIFACT_DIGEST=sha256:796d734fe0f3074319d4471e691ce356f4fe16d7661f8aee5223d48f1cf521c1
RECORD_CAMPAIGN=PASS
RECORD_ADJUDICATION=FAIL
REPLAY=NOT_RUN
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

The downloaded artifact ZIP was re-hashed before inspection and matched the GitHub artifact digest exactly.

## First material Step-15 failure

Step 14 (`Execute 33-parent record campaign`) completed successfully. Step 15 (`Adjudicate record behavior and minimum Decision/RNG obligations`) failed before path-summary, Decision, or RNG adjudication because the parent-runtime predicate found non-PASS parent rows.

The exact Step-15 exception prefix and first eight rows reproduced from the immutable artifact using the workflow's source-commit adjudicator are:

```text
WS33_G_SVAR_EVENT_PARENT_RUNTIME=FAIL [['forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8', '1', '1', 'f3988b96-9e00-445c-b3e1-6b2df9b13dac', 'Ingenious Smith', 'ChangesZone', 'TRIGGER', '', 'TrigDig', 'Dig', 'FAIL', '0', '0', '0'], ['forge-behavior-v2:1b1d899f942620f8251e98ad58577e873d18c540', '1', '1', '2598294c-a9a7-4bef-a562-23f297a80536', "Songbirds' Blessing", 'Attacks', 'TRIGGER', '', 'TrigDigUntil', 'DigUntil', 'FAIL', '1', '1', '0'], ['forge-behavior-v2:1b6ac7024c9a66f59567a68206eac59e77da11d2', '1', '1', 'fcbe14c4-1b0d-486f-bb9c-0fed452668cb', 'Faerie Mechanist', 'ChangesZone', 'TRIGGER', '', 'TrigDig', 'Dig', 'FAIL', '0', '0', '0'], ['forge-behavior-v2:1d94bfd1ff6b0605a685b73e1f5547020edd08c3', '1', '1', '96b909ab-55f1-4cde-a675-2504de3da772', 'Cavalier of Thorns', 'ChangesZone', 'TRIGGER', '', 'TrigDig', 'Dig', 'FAIL', '0', '0', '0'], ['forge-behavior-v2:1e26d641fbb923995b2cfadf1023aa936c4159f8', '1', '1', '2ae71e86-4400-4a30-9077-4d57a43e7395', 'Risen Reef', 'ChangesZone', 'TRIGGER', '', 'TrigPeek', 'PeekAndReveal', 'FAIL', '0', '0', '0'], ['forge-behavior-v2:1ecf14ac9a8cbbf713da5646b207d0294d4d5c21', '1', '1', 'd47fc902-51f7-4ad1-8ee4-c973e32192b8', 'Sage Owl', 'ChangesZone', 'TRIGGER', '', 'TrigRearrange', 'RearrangeTopOfLibrary', 'FAIL', '0', '0', '0'], ['forge-behavior-v2:242680ed5d889cd7f00fc41e2e70ec8945aaf9c1', '1', '1', 'b8602f19-6fc2-43c4-b0c4-2cd11d5dbda2', 'Keen Duelist', 'Phase', 'TRIGGER', '', 'TrigReveal', 'PeekAndReveal', 'FAIL', '0', '0', '0'], ['forge-behavior-v2:2519ac7e9366fb5eea8493851240990c846924ae', '1', '1', '5dec1b09-4df0-4e9b-9dca-b80134be3343', "N'Yami-Class Mother Ship", 'DamageDone', 'TRIGGER', '', 'TrigDig', 'Dig', 'FAIL', '1', '1', '0']]
```

The first failed parent in artifact order is `forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1` (`Ingenious Smith`, `ChangesZone`): parent status `FAIL`, trigger admissions `0`, target bindings `0`, target executions `0`.

## Root cause

Classification: **event-fixture defect**.

The Event harness' `dispatchSourceEvent` constructs the synthetic `ChangesZone` run parameters as:

```java
rp.put(AbilityKey.Origin, ZoneType.Hand);
rp.put(AbilityKey.Destination, ZoneType.Battlefield);
```

Pinned Forge production `GameAction.changeZone` constructs the same fields as zone-name strings:

```java
runParams.put(AbilityKey.Origin, zoneFrom != null ? zoneFrom.getZoneType().name() : null);
runParams.put(AbilityKey.Destination, zoneTo.getZoneType().name());
```

Pinned `TriggerChangesZone.performTest` compares the trigger's string `Origin$` / `Destination$` values against those run-parameter values. The harness' enum-valued fixture therefore fails the production trigger predicate before `runSingleTriggerInternal`, so the post-legality admission observer correctly records `0`.

This diagnosis is source-derived against Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928` and directly verified against artifact `9910414457`.

## Why this must be repaired first

Step 15 stops at the parent-runtime predicate before effective-path, Decision, or RNG obligations. Later parent failures (including admitted-but-not-resolved rows) are therefore later symptoms and must not be repaired before rerunning with the first event-fixture defect removed.

No actual-card behavior coverage is promoted. No Rules-Core defect is inferred from this failure.

## Narrow systemic repair scope

Change only the common `ChangesZone` event fixture in `ws33_prepare_g_svar_event_harness.py` so `AbilityKey.Origin` and `AbilityKey.Destination` use the exact production value shape (`String` zone names) emitted by pinned `GameAction.changeZone`.

Forbidden alternatives remain forbidden: no card-name branch, no path-ID branch, no direct target-SVar entry, no `TriggerHandler` bypass, no fabricated Decision/RNG evidence, no silent fallback.

## Resume

1. Update the canonical handoff with this adjudication.
2. Repair the `ChangesZone` fixture value shape only.
3. Commit the repair separately.
4. Allow exactly one `ws33-g3-svar-event-runtime.yml` run from that repair commit.
5. Persist the new run/job/source identity before any further repair.
6. Adjudicate that run to terminal and, on failure, again stop at its first material failure.
