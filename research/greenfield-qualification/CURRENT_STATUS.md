# Commander Simulator Next — Current Integration Status

Date: 2026-08-29  
Canonical integration branch: `work/91-semantic-failure-cross-qualification-20260829`

```text
WS91_WORKSTREAM_COMPLETE                = TRUE
WS13_ELIGIBLE                           = FALSE
INITIAL_ARCHITECTURE_DECISION_FROZEN    = FALSE
READY_FOR_GREENFIELD_BUILD              = FALSE
READY_FOR_TRUSTED_REAL_DECK_SIMULATION  = FALSE
PRODUCTION_REPOSITORY_CREATED            = FALSE
```

## Retained qualified runtime anchor

WS91 found no successor change that replaces or mutates the WS90 qualified runtime implementation. The retained runtime anchor therefore remains:

- head: `55820618e7243bd5ba8cfa33c3148cea8c166c73`
- tree: `3706900d49c6ef61690c227bb7b4c0067fbcfb44`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- WS90 run/job: `33250119165` / `99094251297`
- WS90 artifact: `9714119110`
- artifact SHA-256: `d5bdb8b59045c78c5c3774bac1f9091c7b32327834eea9abf106412452cdcb4c`

WS14–WS25 additions are qualification workflows, research evidence, witness shards, and test/overlay adapters. Because they do not replace the retained WS90 runtime on WS91, Q1–Q5 and Q7 were not rerun merely for reassurance.

## WS91 cross-gate adjudication

| Gate | WS91 result | Evidence / qualification boundary |
|---|---|---|
| Q0 provenance/schemas | **PASS** | WS90 base plus live WS14–WS25 branch heads/trees, ancestry, changed-file ownership, runs/jobs, artifact IDs/digests and exact Forge pin independently checked |
| Q1 strict decision externalization | **PASS — NO_RERUN** | retained WS90 boundary; no successor change invalidated the qualified runtime decision path |
| Q2 hidden information | **PASS — NO_RERUN** | retained WS90/WS05 principal-scoped boundary; WS22 reused the exact detector without modifying it |
| Q3 RNG / semantic replay | **PASS — NO_RERUN** | retained WS90/WS06 fresh-process semantic replay boundary; WS22 reused the comparator without modifying it |
| Q4 process isolation | **PASS — PROCESS_PER_GAME — NO_RERUN** | retained WS90/WS08 process-per-game boundary; same-JVM multi-game isolation remains unqualified |
| Q5 Commander / multiplayer | **PASS — NO_RERUN** | retained WS90 combined-runtime qualification; successor work did not alter Commander/multiplayer runtime code |
| Q6 actual-card behavior | **FAIL_CLOSED** | WS24 immutable gate: 13/174 primitives PASS, 161 PARTIAL, 1,800 unresolved source bindings; 664/1,678 identities PARTIAL and 1,014 UNKNOWN |
| Q7 differential adjudication | **PASS — SCOPE LIMITED — NO_RERUN** | retained WS90 scope; no successor change invalidated its two shared scenarios |
| Q8 license / third-party | **DEFERRED** | WS13 is not eligible because Q6 and failure semantics are not PASS; no license topology is issued by WS91 |
| FAILURE_SEMANTICS | **FAIL_CLOSED** | WS25 immutable gate: all 16 categories accounted for, but production-runtime binding for `CARD_BEHAVIOR_FAILURE` remains UNKNOWN |

## Independently verified successor evidence

### WS24 — Q6 semantic integration

- final HEAD/tree: `7267a6ead4fbc7c72a0d0e2e8da1c0e5ca8e34e6` / `8f1db090569e3d4079280fd5d8b8ad39b31ba0e6`
- tested HEAD/tree: `5b7dc610caadaa3d9539e26bca3bda5879955fe0` / `6647325ed48bcadb8439812006d9fa6ca4093e67`
- run/job: `33273280712` / `99155505569` — SUCCESS
- artifact: `9720751546`
- artifact SHA-256: `512c4d9f1fdae11aab8bb6145af2df02e3d2c42205ac42c17d521fcd34e267b9`
- artifact internal SHA-256 manifest: independently verified
- `Q6_ACTUAL_CARD_BEHAVIOR = FAIL_CLOSED`

The only 13 PASS primitives are backed by exact-pinned Forge state witnesses from WS16 (`2`) and WS17 (`11`). All have immutable trace hashes and `stdout_only=false`. No global Q2/Q3 result is promoted to card behavior proof.

### WS25 — failure-semantics integration

- final HEAD/tree: `f40e12bc321223ec1a4918fa3f0e425ec5651ba2` / `ff2f2a9bc830d14df350862273c9076a07e644f6`
- tested HEAD/tree: `05cf89a5ef515f84fc81ddd4db9aba788704df06` / `bac6cc5600c20b879e0d826959a728d1b7245777`
- run/job: `33275091071` / `99160294360` — SUCCESS
- artifact: `9721261751`
- artifact SHA-256: `2e1bc7c04eafecf211b6647fb97ce490c09cfca250c038dd35f22e54ecb641cf`
- artifact internal SHA-256 manifest: independently verified
- production-reachable untyped outcomes: exactly `1`
- exact unbound category: `CARD_BEHAVIOR_FAILURE`
- `FAILURE_SEMANTICS = FAIL_CLOSED`

WS20, WS21 and WS22 independently bind the actual production-facing action/rules, engine/transport, replay and hidden-information failure paths they own. WS23 proves a qualifier-side `CARD_BEHAVIOR_FAILURE` detector, but explicitly does not prove a production-runtime callsite.

## Architecture progression blockers

### Q6

`161` atomic primitives remain without PASS witnesses and `1800` WS14 source bindings remain unresolved. The next Q6 work must close these systemically with actual exact-pinned Forge execution, authoritative legal decisions, semantic state assertions, immutable traces, and decision/RNG tapes where relevant. Parsing, source presence, global-contract inheritance and card-name production exceptions do not qualify.

### Failure semantics

`CARD_BEHAVIOR_FAILURE` must be bound to a real production-runtime semantic verifier/capture path. A controlled actual mismatch at that path must emit the typed outcome and prove no failed-state commit, fallback coercion, or private-data disclosure.

## Progression decision

The two mandatory WS91 questions are both negative:

```text
Q6_ACTUAL_CARD_BEHAVIOR_PASS                     = FALSE
FAILURE_SEMANTICS_PASS                           = FALSE
COMPATIBLE_TOPOLOGY_WITH_BOTH_PASS               = FALSE
WS13_ELIGIBLE                                    = FALSE
```

Q8 remains deferred. No architecture freeze is authorized, `moeendres-png/commander-simulator-next` must not be created, and no production build may start from this status.

Machine-readable detail is in `WS91_CROSS_QUALIFICATION.json`; the fail-closed topology handoff is `WS91_TOPOLOGY_HANDOFF.md`.
