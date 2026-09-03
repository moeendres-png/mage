# G3 NON-AF EVENT RUNTIME — RUN 33818067742 FAILURE

Evidence classification: `DIRECTLY_VERIFIED`.

## Immutable run identity

```ini
RUN=33818067742
JOB=100854474552
SOURCE_HEAD=8446cfc72060156db63237cb7c4b00045ef72fbb
SOURCE_TREE=f625b3cbaf0825bc17934e667858adf2defbec57
ARTIFACT=9917297622
ARTIFACT_DIGEST=sha256:34a0f2185d19d19724b7e1d3c7dcffc0d1da764f6d4c5180f2bf2622aee806ea
FIRST_MATERIAL_FAILURE_STEP=14
RECORD_CAMPAIGN=NOT_EXECUTED_TEST_BODY
RECORD_ADJUDICATION=NOT_RUN
REPLAY=NOT_RUN
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

The downloaded artifact ZIP was independently SHA-256 hashed and matched the GitHub digest exactly.

## First material failure

Steps 1–13 succeeded, including both the lineage-enhanced Event harness transform and the authoritative request-trace transform:

```text
WS33_G_SVAR_EVENT_HARNESS=PASS parents=33 effective_paths=32 trigger_legality=FORGE_TRIGGER_HANDLER target_direct_entry=FALSE parent_observer=POST_LEGALITY_ADMISSION target_observer=POST_FIZZLE_PRE_RESOLVE resolution_lineage=OBSERVATION_ONLY
WS33_G_REQUEST_TRACE_PATCH=PASS mode=observer_only payload=opaque_authoritative_option_ids write_abi=DIRECT_OR_EVENT_OR_LINEAGE_EVENT
```

Step 14 failed during Maven `testCompile`, before the qualification test body executed:

```text
[ERROR] .../forge/net/Ws33GSVarEventQualificationTest.java:[109,59] cannot find symbol
  symbol:   class TreeMap
  location: class forge.net.Ws33GSVarEventQualificationTest
[ERROR] .../forge/net/Ws33GSVarEventQualificationTest.java:[109,93] cannot find symbol
  symbol:   class TreeMap
  location: class forge.net.Ws33GSVarEventQualificationTest
```

## Root cause

Classification: **diagnostic harness compile defect**.

The observation-only `mapHash` helper introduced by diagnostic commit `4c97b95e...` used unqualified `TreeMap`, but the inherited Direct-G Java harness imports do not include `java.util.TreeMap`. This prevents compilation before any runtime semantics are exercised.

No Forge runtime behavior, trigger reachability, target resolution, Decision/RNG, hidden-state behavior, or coverage was adjudicated by this run.

## Narrow systemic repair scope

Change only the generated diagnostic helper from unqualified `TreeMap` to fully qualified `java.util.TreeMap` (or equivalently add the import). Prefer the fully qualified type to avoid modifying the inherited import ABI. Do not change the map fingerprint algorithm, lineage fields, `matchesTarget`, `targetExecutions`, event fixtures, request trace, Forge overlays, or any rules behavior.

## Resume

1. Update canonical handoff with this compile-only failure.
2. Repair only the `TreeMap` qualification in `ws33_prepare_g_svar_event_harness.py`.
3. Commit separately.
4. Allow exactly one event-runtime retry from that repair.
5. Persist run/job/source identity immediately.
6. Terminally adjudicate and require an artifact containing `resolution-lineage.tsv` before resolving the frozen first-parent `1/1/0` question.
