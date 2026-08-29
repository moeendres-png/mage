# WS25 — Failure Semantics Integration — Handoff

`WORKSTREAM_COMPLETE = TRUE`

## Scope and provenance

WS25 independently re-adjudicates the complete 16-category authoritative failure-outcome vocabulary after WS20–WS23, without rerunning already-qualified predecessor suites. It consumes predecessor evidence read-only and preserves the retained WS12 decision/process paths unless a successor workstream supplied stronger actual-path evidence.

- Repository: `moeendres-png/mage`
- Branch: `work/ws25-failure-semantics-integration-20260829`
- Base / retained WS12 final HEAD: `80743bdbc2950b00e422f3deb38f04111f30a4d4`
- Base tree: `9a2a52932a0d69dcf06c2392cddcf40b47e810cc`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- `TESTED_HEAD = 05cf89a5ef515f84fc81ddd4db9aba788704df06`
- `TESTED_TREE = bac6cc5600c20b879e0d826959a728d1b7245777`
- `FINAL_HANDOFF_HEAD = SELF`; this documentation-only commit is reported externally after creation.

## Verified dependencies

The WS25 integration run independently verified the live final branch refs and immutable qualification artifacts before consuming them.

### WS20 — action + rules

- Final/tested HEAD: `df146cd5aa404c2c371bc1591416d4bf57dbf2cc`
- Run: `33254049343`
- Job: `99104581314`
- Artifact: `ws20-failure-action-rules`
- Artifact ID: `9715271475`
- Artifact SHA-256: `0945f0f15bc54ebcbbf4bed81999c99191b4ef5f5f4149ec61a52ddc4082fecb`
- `ACTION_NOT_COMPLETABLE = PASS`
- `UNSUPPORTED_RULES_PATH = PASS`

### WS21 — engine + transport

- Qualified executable HEAD: `cfd9ca96a796a825b0c70d7caff849ae49883752`
- Final handoff HEAD: `a016ac70778c0784857f5e3247629e5866a16e15`
- Run: `33254238155`
- Job: `99105065883`
- Artifact: `ws21-failure-engine-transport`
- Artifact ID: `9715407935`
- Artifact SHA-256: `2b4456226526e941e87d4b8f0c0f54e3410635e6382ddef8e3812b98eefbec35`
- `ENGINE_FAILURE = PASS`
- `TRANSPORT_FAILURE = PASS`

### WS22 — replay + hidden information

- Tested executable HEAD: `984f78737fc682abb58da9c89ae7738d0224c41b`
- Final handoff HEAD: `45f5691ab4cc1e8a2e4a0904b041ef08a1613612`
- Run: `33255343659`
- Job: `99107951779`
- Artifact: `ws22-failure-replay-hidden-33255343659`
- Artifact ID: `9715695346`
- Artifact SHA-256: `43f5b3f76989dc850b73356cb427316d1bf8dc7d109fa57d4691750b92d33a6d`
- `REPLAY_DIVERGENCE = PASS`
- `HIDDEN_INFO_VIOLATION = PASS`
- `Q2_PRINCIPAL_HIDDEN_INFORMATION = NO_RERUN`
- `Q3_SEMANTIC_REPLAY = NO_RERUN`

### WS23 — card-behavior semantic verifier

- Tested executable HEAD: `bb066962376d48bbfa1ce42b96b4c8b57c30d72f`
- Final handoff HEAD: `b773d490f2e5610a72499f8633ef3e3b82be3757`
- Run: `33273319809`
- Job: `99155610511`
- Artifact: `ws23-card-behavior-failure-evidence`
- Artifact ID: `9720758445`
- Artifact SHA-256: `f9084d2166460b4ea2a2c85af64aceee406003d8fc160030ff1846e8b401cba3`
- qualifier/verifier `CARD_BEHAVIOR_FAILURE = PASS`
- `production_binding = QUALIFIER_ONLY`
- implemented verifier `production_reachable = false`

## Dedicated WS25 qualification evidence

- Workflow run: `33275091071`
- Job: `99160294360`
- Run result: `SUCCESS`
- Tested HEAD: `05cf89a5ef515f84fc81ddd4db9aba788704df06`
- Tested tree: `bac6cc5600c20b879e0d826959a728d1b7245777`
- Artifact: `ws25-failure-semantics-integration`
- Artifact ID: `9721261751`
- Artifact SHA-256: `2e1bc7c04eafecf211b6647fb97ce490c09cfca250c038dd35f22e54ecb641cf`

The workflow independently re-downloaded the four immutable successor artifacts and generated/hash-verified:

- `FAILURE_SEMANTICS_GATE.v2.json`
- `FAILURE_SEMANTICS_GATE.v2.md`
- `FAILURE_SEMANTICS_MATRIX.v2.json`
- `FAILURE_SEMANTICS_TRACE_INVENTORY.v2.json`
- `WS25_HASHES.sha256`

The run directly emitted:

- `WS25_CATEGORY_COUNT=16`
- `WS25_PRODUCTION_REACHABLE_UNTYPED=1`
- `WS25_CARD_BEHAVIOR_PRODUCTION_BINDING=UNKNOWN`
- `FAILURE_SEMANTICS=FAIL_CLOSED`
- `WORKSTREAM_COMPLETE=TRUE`

## Final 16-category adjudication

| Category | Production adjudication | Evidence source |
|---|---|---|
| `SUCCESS` | PASS | retained WS12 exact decision path |
| `PLAYER_CANCELLED` | PASS | retained WS12 exact decision path |
| `ACTION_NOT_COMPLETABLE` | PASS | WS20 actual runtime guard |
| `ILLEGAL_RESPONSE` | PASS | retained WS12 exact decision path |
| `MALFORMED_RESPONSE` | PASS | retained WS12 exact decision path |
| `STALE_RESPONSE` | PASS | retained WS12 exact decision path |
| `WRONG_ACTOR` | PASS | retained WS12 exact decision path |
| `TIMEOUT` | PASS | retained WS12 exact decision path |
| `UNSUPPORTED_DECISION_PATH` | PASS | retained WS12 exact decision path |
| `UNSUPPORTED_RULES_PATH` | PASS | WS20 actual Rules Core guard |
| `ENGINE_FAILURE` | PASS | WS21 actual engine-side boundary |
| `TRANSPORT_FAILURE` | PASS | WS21 actual transport boundary |
| `PROCESS_FAILURE` | PASS within retained scoped process contract | retained WS12 process witness |
| `REPLAY_DIVERGENCE` | PASS | WS22 exact WS06 semantic replay comparator |
| `HIDDEN_INFO_VIOLATION` | PASS | WS22 exact WS05 principal-authorization detector |
| `CARD_BEHAVIOR_FAILURE` | **FAIL_CLOSED / production binding UNKNOWN** | WS23 qualifier-only detector |

## Why the aggregate gate remains fail-closed

The retained authoritative WS12 outcome schema marks `CARD_BEHAVIOR_FAILURE` as `production_reachable=true`. WS23 successfully proves that its semantic verifier detects a controlled expected/actual mismatch, emits the typed category, does not commit failed state, does not leak semantic values, and is distinct from `ENGINE_FAILURE`.

However, WS23 also correctly establishes that this verifier is `QUALIFIER_ONLY`; no actual candidate production-runtime callsite was proven. WS25 therefore does not rewrite the contract's reachability and does not invent a runtime adapter merely to obtain a green aggregate gate.

Consequently:

- production-reachable untyped outcomes: exactly `1`
- exact untyped category: `CARD_BEHAVIOR_FAILURE`
- observed prohibited fallback handlers: `0`
- fallback absence on the unbound production card-behavior path: `UNKNOWN`
- failed-state commits observed for failure categories: `0`
- hidden-information-safe payload checks: PASS for all evidenced paths

## Hard-gate result

True:

- `ALL_16_CATEGORIES_ACCOUNTED_FOR`
- `SIX_SUCCESSOR_PRODUCTION_BINDINGS_PASS`
- `RETAINED_WS12_TYPED_PATHS_PRESERVED`
- `CARD_BEHAVIOR_QUALIFIER_DETECTOR_PASS`
- `OBSERVED_PROHIBITED_FALLBACKS_ZERO`
- `HIDDEN_INFO_SAFE_PAYLOADS`
- `FAILED_STATE_COMMITS_ZERO`
- `Q2_Q3_NO_RERUN_PRESERVED`

False, deliberately fail-closed:

- `CARD_BEHAVIOR_PRODUCTION_BINDING_CLOSED`
- `REACHABLE_UNTYPED_FAILURES_ZERO`
- `REACHABLE_FALLBACK_HANDLING_ZERO_PROVEN`

## Regression policy

- `Q2_PRINCIPAL_HIDDEN_INFORMATION = NO_RERUN`
- `Q3_SEMANTIC_REPLAY = NO_RERUN`

WS25 changes only the integration/adjudication layer. It does not modify the qualified WS05 or WS06 detector boundaries, so a full Q2/Q3 rerun is neither required nor justified.

## Evidence classification

- dependency branch/run/artifact identity checks: `DIRECTLY_VERIFIED`
- retained source/boundary mappings: `CODE_DERIVED`
- WS20/WS21/WS22 actual-path runtime detector evidence: `TECHNICALLY_CONFORMANT`
- WS23 qualifier-side semantic detector: `TECHNICALLY_CONFORMANT`
- production runtime binding for `CARD_BEHAVIOR_FAILURE`: `UNKNOWN`
- aggregate WS25 evidence class: `UNKNOWN` because one authoritative production-reachable category remains unbound

## Final result

- `WORKSTREAM_COMPLETE = TRUE`
- `FAILURE_SEMANTICS = FAIL_CLOSED`
- `production_reachable_untyped_failure_outcomes = 1`
- `production_reachable_fallback_observed_count = 0`
- `CARD_BEHAVIOR_FAILURE production binding = UNKNOWN`
- `Q2 = NO_RERUN`
- `Q3 = NO_RERUN`
- `ARCHITECTURE_FREEZE = NOT AUTHORIZED BY THIS WORKSTREAM`

The exact remaining successor requirement is a new, separate production-binding workstream for `CARD_BEHAVIOR_FAILURE`: bind a real runtime semantic-verifier/capture path, induce a real mismatch at that path, emit the authoritative typed failure, and prove no state commit, fallback, or private-data disclosure. That future requirement is an evidence result of WS25; it does not make WS25 itself incomplete.

This final handoff commit is documentation-only and does not alter the tested integrator or immutable evidence. No qualification rerun is required solely for this commit.
