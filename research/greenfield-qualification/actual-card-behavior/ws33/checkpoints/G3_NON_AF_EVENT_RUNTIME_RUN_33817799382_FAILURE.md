# G3 NON-AF EVENT RUNTIME — RUN 33817799382 FAILURE

Run/artifact facts are `DIRECTLY_VERIFIED`. The Step-12 root cause is `CODE_DERIVED` from the exact source commit plus artifact logs and deterministic reproduction of the failing request-trace ABI anchor.

## Immutable run identity

```ini
RUN=33817799382
JOB=100853681886
SOURCE_HEAD=4c97b95ea3777f20ed2239f8a38aae82b2abc217
SOURCE_TREE=413096e4ba7bbb131edc31ebaf7534b519647fd3
ARTIFACT=9917183980
ARTIFACT_DIGEST=sha256:9b15ab387e0bb920e800e38d13d96030bbd7371b05b93ff7e9919ceaf79051ac
FIRST_MATERIAL_FAILURE_STEP=12
RECORD_CAMPAIGN=NOT_RUN
RECORD_ADJUDICATION=NOT_RUN
REPLAY=NOT_RUN
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

The downloaded ZIP was independently SHA-256 hashed and matched the GitHub artifact digest exactly.

## Step state

Steps 1–11 succeeded. Step 12 (`Prepare 33-parent event harness with request trace`) failed. Java setup and runtime/adjudication/replay/source-chain steps were skipped; evidence upload succeeded.

Artifact diagnostics prove the event harness transform itself completed:

```text
WS33_G_SVAR_EVENT_HARNESS=PASS parents=33 effective_paths=32 trigger_legality=FORGE_TRIGGER_HANDLER target_direct_entry=FALSE parent_observer=POST_LEGALITY_ADMISSION target_observer=POST_FIZZLE_PRE_RESOLVE resolution_lineage=OBSERVATION_ONLY
```

`diagnostic/request-trace.log` is empty because the following request-trace transform exited before its PASS print.

## First failure and root cause

Classification: **Harness / instrumentation ABI defect** introduced by the observation-only diagnostic change; no Forge runtime was executed.

The generated event harness now writes:

```java
writeEvidence(...);
writeParentEvidence(outDir);
writeResolutionLineage(outDir);
PlayerControllerHuman.setExternalDecisionProviderFactory(null);
```

But `ws33_instrument_g_authoritative_requests.py` recognizes only the pre-diagnostic Event ABI:

```java
writeEvidence(...);
writeParentEvidence(outDir);
PlayerControllerHuman.setExternalDecisionProviderFactory(null);
```

and the Direct ABI. Therefore its `replace_one_of` finds zero recognized anchors. Reproducing that exact source predicate yields:

```text
WS33_G_REQUEST_TRACE_PATCH=FAIL request trace write ABI: expected exactly one ABI anchor, got {'writeEvidence(outDir,mode,cases,evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);PlayerControllerHuman.setExternalDecisionProviderFactory(null);': 0, 'writeEvidence(outDir,mode,uniqueCases(cases),evidence,allRng,rngPath,allDecisions,decisionPath,result,outer);writeParentEvidence(outDir);PlayerControllerHuman.setExternalDecisionProviderFactory(null);': 0}
```

This occurs after the event harness generator PASS and before any runtime execution, so it cannot change or adjudicate the previously frozen `1/1/0` reachability failure.

## Narrow systemic repair scope

Extend the request-trace transform's supported Event write ABI to include the diagnostic-only lineage writer while preserving all existing Direct/Event ABIs fail-closed. The corrected diagnostic Event chain must become:

```java
writeEvidence(...);
writeParentEvidence(outDir);
writeResolutionLineage(outDir);
writeWs33DecisionRequests(outDir);
PlayerControllerHuman.setExternalDecisionProviderFactory(null);
```

Do not weaken `replace_one_of`; mixed/ambiguous ABIs must remain rejected. Do not alter the lineage telemetry, target matcher, `targetExecutions` gate, Forge semantics, Decision/RNG payloads, or coverage.

## Resume

1. Update the canonical handoff with this pre-runtime diagnostic failure.
2. Repair only the request-trace Event ABI support.
3. Commit separately.
4. Allow exactly one event-runtime retry from that repair commit.
5. Persist its run/job/source identity immediately.
6. Adjudicate terminally; only a runtime artifact containing `resolution-lineage.tsv` may answer the unresolved first-parent reachability question.
