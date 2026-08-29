# Commander Simulator Next — Current Integration Status

Date: 2026-08-29  
Canonical integration branch: `work/90-integration-cross-qualification-20260828`

```text
INTEGRATION_COMPLETE                    = TRUE
INITIAL_ARCHITECTURE_DECISION_FROZEN   = FALSE
READY_FOR_GREENFIELD_BUILD             = FALSE
READY_FOR_TRUSTED_REAL_DECK_SIMULATION = FALSE
PRODUCTION_REPOSITORY_CREATED           = FALSE
```

## Reproducible integrated runtime anchor

All WS01–WS10 branch slices were live-verified against audit base
`c0e42fb42c4a603aff4a76b1284f8271c12bfd42` / tree
`fb06c61dd87b4b742722925cd7374d8f037e1f47` and integrated in dependency order.
The cross-qualified runtime source executed by WS90 is:

- head: `55820618e7243bd5ba8cfa33c3148cea8c166c73`
- tree: `3706900d49c6ef61690c227bb7b4c0067fbcfb44`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- WS90 run/job: `33250119165` / `99094251297`
- WS90 artifact: `9714119110`
- artifact SHA-256: `d5bdb8b59045c78c5c3774bac1f9091c7b32327834eea9abf106412452cdcb4c`

The final status-document commit is intentionally not used as runtime proof;
`55820618…` is the exact tree executed by the integrated qualification run.

## Cross-gate adjudication

| Gate | WS90 result | Evidence / qualification boundary |
|---|---|---|
| Q0 provenance/schemas | **PASS** | all ten branch heads/trees and audit-base ancestry verified live; machine-readable gates and exact engine pins checked |
| Q1 strict decision externalization | **PASS** | 4P full game; 699 accepted typed decisions; 109 controller + 15 blocking-GUI semantic census complete; production-reachable untyped/fallback decisions = 0 |
| Q2 hidden information | **PASS** | 4P principal campaign; pilot-visible hidden-info leaks = 0; cross-principal decision leaks = 0 |
| Q3 RNG / semantic replay | **PASS** | three fresh processes A/B/C; state, RNG-event and decision-event divergences = 0 |
| Q4 process isolation | **PASS — PROCESS_PER_GAME** | combined WS01+WS05+WS06+WS08 build; parallel 4P games + worker fault injection; same-JVM multi-game isolation is not qualified |
| Q5 Commander / multiplayer | **PASS** | WS90 reran WS07 on the combined WS01+WS05+WS06 Forge stack: 42/42 semantic rows, 4P mandatory scenarios and 2P–5P subsets PASS |
| Q6 actual-card behavior | **FAIL** | WS10's `Q6=PASS` claim is rejected: 1,678 cards are loadable/constructable, but per-card decision/hidden/replay flags inherit global dependency booleans and 0/1,678 identities have direct semantic `FULL` proof |
| Q7 differential adjudication | **PASS — SCOPE LIMITED** | two shared Forge/XMage scenarios; Forge side freshly requalified by WS90; phase.rs and Manabrew remain unsupported/unknown for this adapter; no engine-majority rules authority |
| Q8 license / third-party | **DEFERRED_PENDING_ARCHITECTURE_SELECTION** | WS03 subgate PASS, but `LICENSE_DECISION_COMPLETE = FALSE`; architecture-dependent legal implications remain explicit unknowns |
| Integrated failure semantics | **FAIL / INCOMPLETE** | no unified verified taxonomy covers all required success/cancel/not-completable/response/rules/engine/transport/process/replay/hidden-info/card-behavior outcomes |

## Mandatory zero / hard metrics

```text
PILOT_VISIBLE_HIDDEN_INFO_LEAKS          = 0
CROSS_PRINCIPAL_DECISION_LEAKS           = 0
production_reachable_untyped_decisions   = 0
production_reachable_fallback_decisions  = 0
semantic replay fresh-process A/B/C      = PASS
semantic_state_divergences               = 0
rng_event_divergences                    = 0
decision_event_divergences               = 0
4P primary semantic qualification        = PASS
```

## Workstream disposition

WS01, WS02, WS03, WS04, WS05, WS06, WS07, WS08 and WS09 are accepted within
their stated evidence boundaries. WS03 is not promoted to Q8 PASS; WS04 is
provenance-only; WS08 qualifies process-per-game only; WS09 is a narrow two-
scenario differential gate.

WS10's branch and evidence harness are retained for audit, but its behavioral
`Q6_ACTUAL_CARD_COVERAGE = PASS` conclusion is rejected by integration. The
classifier sets `DECISION_COMPLETE`, `HIDDEN_INFO_SAFE` and `REPLAY_SAFE` from
global WS01/WS05/WS06 PASS booleans after regex reachability classification,
and requires dedicated card behavior only for hard suspicious source markers.
That is not actual identity-level behavioral proof.

## Architecture-freeze blockers

1. `Q6_ACTUAL_CARD_BEHAVIOR = FAIL`.
2. `FAILURE_SEMANTICS = FAIL_INCOMPLETE`.
3. `Q8 = DEFERRED_PENDING_ARCHITECTURE_SELECTION`.

Therefore an Architecture Freeze is prohibited and the private production
repository must not be created. Exact machine-readable adjudication is in
`WS90_INTEGRATION_ADJUDICATION.json`; the next dependency wave is specified in
`NEXT_HANDOFF.md`.
