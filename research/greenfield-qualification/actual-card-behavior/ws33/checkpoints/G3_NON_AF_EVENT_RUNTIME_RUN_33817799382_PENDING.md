# G3 NON-AF EVENT RUNTIME — RUN 33817799382 PENDING

Evidence classification: `UNKNOWN` until terminal run/artifact adjudication.

## Run identity

```ini
DIAGNOSTIC_COMMIT=4c97b95ea3777f20ed2239f8a38aae82b2abc217
SOURCE_TREE=413096e4ba7bbb131edc31ebaf7534b519647fd3
RUN=33817799382
JOB=100853681886
WORKFLOW=.github/workflows/ws33-g3-svar-event-runtime.yml
RUN_NUMBER=5
RUN_ATTEMPT=1
OBSERVED_STATUS=in_progress
CONCLUSION=PENDING
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

## Observation-only diagnostic represented by this run

The only new instrumentation since terminal run `33816948410` adds `resolution-lineage.tsv` and in-memory lineage fields to the existing non-AF event harness. It records source-proven admitted ability identity plus every MagicStack post-fizzle/pre-resolve observer callback under the active parent key.

The existing qualification predicate is intentionally unchanged:

```text
triggerAdmissions == 1
targetBindings == 1
targetExecutions >= 1
```

The existing `matchesTarget` implementation is also unchanged. The new telemetry does not alter legality, targets, choices, stack order, fizzle adjudication, resolution, Decision/RNG handling, hidden information, or coverage.

## Diagnostic question

For the first previously failing parent (`Ingenious Smith`, `ChangesZone`, path `forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1`), distinguish:

1. `resolutionCallbacks == 0`: no post-fizzle MagicStack resolution callback occurred under the active parent, so investigate production stack placement/non-resolution; or
2. `resolutionCallbacks > 0 && targetExecutions == 0`: a production resolution callback occurred but the current exact-script matcher did not recognize it; compare admitted/resolving IDs, source-trigger IDs, host/API and map fingerprints before repairing measurement identity.

No repair is authorized from this pending checkpoint alone.

## Serial invariant

Run `33817799382` is the single diagnostic retry produced by commit `4c97b95ea3777f20ed2239f8a38aae82b2abc217`. Do not start another runtime run until this run is terminal, its immutable artifact/digest is secured, the first material result is adjudicated, and that adjudication is persisted.
