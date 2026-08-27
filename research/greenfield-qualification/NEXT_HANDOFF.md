# Commander Simulator Next — Next Handoff

Date: 2026-08-28

## Entry state

```text
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
FIRST_BLOCKING_GATE = DECISION_EXTERNALIZATION
FIRST_BLOCKING_SUBGATE = FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE
```

Do not create `moeendres-png/commander-simulator-next` and do not use the old
Commander-Lab checkout as a Rules Core source.

## Current exact inputs

- Research input head: `7f843a29808c086f960128585b49bb18a7ec381a`.
- Research input tree: `c7c570a7e88bc7b4d0cced2d9ef88aed5fd9528e`.
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.
- Strict patch SHA-256: `ef10fd59faf63b241b862d1700690bc1668421f00b72541929333f7fe4d1c7e9`.

## Completed in this increment

1. Robust Scryfall gzip/JSONL (and plain JSON array) ingest with deterministic
   Oracle-ID deduplication; current upstream count is 38,626.
2. Fail-closed project union materializer; current result is `NOT_RUN`, 0/1,721
   because only descriptor fragments are present.
3. Research-only typed Forge server boundary for exact Player/Card/entity
   selections, monotonic token, actor/principal, schema/constraint validation,
   atomic application, and explicit timeout/unsupported errors.
4. Static census: 109 controller declarations, 15 blocking GUI decisions, 3
   directly routed entity-selection methods, 106 remaining.
5. Versioned Decision/RNG/State/Tape schemas and semantic-only replay tool.
6. Exact A–T and C01–C22 matrix materialization, all rows marked `NOT_RUN`.
7. Current status, scorecard, architecture, hidden-info, isolation,
   differential, license, and coverage documents synchronized to the same
   provenance boundary.

## Required next work

1. Extend the typed export to every discretionary controller callback and all
   15 blocking GUI decisions, or prove an explicit typed unsupported path is
   unreachable for the complete 4P Commander scope.
2. Add runtime DecisionRequest/DecisionEvent emission and a trusted adapter
   integration test covering valid/invalid/stale/wrong-principal/timeout paths.
3. Rerun the hidden-information assay through that exact boundary; require zero
   principal-scoped leaks across raw transport, logs, exceptions, IDs, hashes,
   and debug output.
4. Instrument named RNG streams, canonical public/principal state digests,
   event tapes, and decision tapes; run three fresh processes with semantic
   equality at every boundary.
5. Rebuild the complete 1,721-identity union from materialized source rows
   (including official precons and explicitly unknown opponent slots) without
   name-based or synthetic promotion.
6. Execute A–T/C01–C22 and per-identity behavior coverage through the same
   boundary, then run differential adjudication against XMage/phase.rs.
7. Only if every Q0–Q8 gate passes, derive the final ADR/scorecard and create
   the private production repository; otherwise preserve `FALSE` and record
   the next exact blocker.

## Guardrails

Google Drive remains read-only. No deck, inventory, purchase, allocation, or
playtest-lab state may be changed. Historical runs may be cited only as
historical context, never as current-head evidence.
