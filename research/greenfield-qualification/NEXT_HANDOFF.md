# Commander Simulator Next — Next Handoff

Date: 2026-08-27

## Entry state

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`

Do not start the production repository and do not inspect Commander-Lab as an architecture prior.

Read first:

1. `CURRENT_STATUS.md`
2. `EXISTING_RUN_RECONCILIATION.md`
3. `DECISION_CENSUS.md` / `.json`
4. `HIDDEN_INFORMATION_ASSAY.md` / `.json`
5. `RNG_INVENTORY.md`
6. `ACTUAL_CARD_REQUIREMENT_MANIFEST.md` / `.json`
7. `ACTUAL_CARD_COVERAGE.md` / `.json`
8. `FINAL_ENGINE_SCORECARD.md`
9. `FINAL_ARCHITECTURE_DECISION.md`

## First blocking gate

`DECISION_EXTERNALIZATION`

Existing evidence must not be rerun:

- Forge broad 2P–5P and RogShai baseline PASS.
- Forge census/RNG run `33095873712`, artifact `9656344793`.
- Forge raw hidden transport run `33095565820`, artifact `9656277015`, 74 hidden identities.
- XMage targeted-v2 run `33089884301`, artifact `9655841512`.
- phase.rs targeted run `33078715204`, artifact `9649312620`; red Commander-inventory step is HARNESS failure, not Rules failure.
- Manabrew isolation-only run `33090536113`, artifact `9654315901`.
- Precon extraction run `33089467077`, artifact `9653672924`.
- Forge neutral card index run `33090672334`, artifact `9654200891`.

## Exact next qualification task

At Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`, build a **research-only Strict External Pilot Qualification Adapter**. This is not the production simulator.

Required gate contract:

```text
Rules Core
-> exact legal choices
-> typed Decision Request
-> external non-AI/non-default Pilot
-> typed Decision Response
-> strict validation
-> Rules Core execution
```

Must prove at runtime for every decision kind reachable from the current actual-card requirement population:

- actor identity is explicit;
- visibility scope is explicit;
- exact legal options are externally represented;
- missing/null response rejects;
- malformed response rejects;
- stale decision rejects;
- wrong actor rejects;
- illegal option rejects;
- timeout invalidates game;
- unknown callback/path invalidates game as `UNSUPPORTED_DECISION_PATH`;
- no `choose first`, `defaultYes`, `defaultOption`, random, AI, silent pass/cancel or best-effort fallback is reachable.

Emit machine-readable registry fields:

```text
decision_kind
backend_source
runtime_trigger
actor
visibility_scope
legal_options
response_schema
validation
invalid_response_test
fallback_present
runtime_test
status
```

Pass conditions:

```text
SILENT_FALLBACKS = 0
PRODUCTION_REACHABLE_UNSUPPORTED_DECISIONS = 0
```

Start with 4P as the primary production topology but retain already-qualified 2P–5P Rules runtime evidence; do not replay those old baseline games merely for confidence.

If this gate passes, the immediate following gates are:

1. principal-scoped hidden-information red team through the exact same boundary;
2. action tape + explicit RNG tape fresh-process A/B/C semantic replay;
3. merged Oracle-identity requirement manifest and actual-card behavior admission through that boundary;
4. remaining complete Commander/rules matrix and common-contract differential adjudication;
5. final license boundary and Architecture Freeze recalculation.

Only after every mandatory gate passes may `INITIAL_ARCHITECTURE_DECISION_FROZEN` become TRUE and a production repository be created.
