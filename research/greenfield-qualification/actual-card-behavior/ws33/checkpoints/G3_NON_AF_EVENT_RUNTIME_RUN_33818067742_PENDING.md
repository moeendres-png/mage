# G3 NON-AF EVENT RUNTIME — RUN 33818067742 PENDING

Evidence classification: `UNKNOWN` until terminal run/artifact adjudication.

```ini
REPAIR_COMMIT=8446cfc72060156db63237cb7c4b00045ef72fbb
SOURCE_TREE=f625b3cbaf0825bc17934e667858adf2defbec57
RUN=33818067742
JOB=100854474552
WORKFLOW=.github/workflows/ws33-g3-svar-event-runtime.yml
RUN_NUMBER=6
RUN_ATTEMPT=1
OBSERVED_STATUS=in_progress
CONCLUSION=PENDING
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

## Narrow repair represented by this run

`ws33_instrument_g_authoritative_requests.py` now accepts a third exact write ABI for the lineage-enhanced Event harness and inserts `writeWs33DecisionRequests(outDir)` after `writeResolutionLineage(outDir)`. Direct and pre-lineage Event ABIs remain supported; ambiguous or mixed anchors still fail closed.

No change was made to the event fixtures, Forge overlays, `matchesTarget`, `targetExecutions`, lineage observer fields, Decision/RNG payload semantics, hidden information, or coverage.

## Serial invariant

This is the single retry from repair commit `8446cfc72060156db63237cb7c4b00045ef72fbb`. Do not start another runtime retry until run `33818067742` is terminal, its artifact/digest is secured, and the first material result is persisted.

## Terminal adjudication target

If Runtime reaches the previously frozen parent failure, use `resolution-lineage.tsv` for `Ingenious Smith/ChangesZone` to distinguish zero resolution callbacks from callback-with-identity-mismatch. Do not repair later event-specific failures before that first distinction is resolved.
