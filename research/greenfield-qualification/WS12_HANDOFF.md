# WS12 unified failure semantics — handoff

`WORKSTREAM_COMPLETE = TRUE`

## Provenance

- `BRANCH = work/ws12-failure-semantics-20260829`
- `BASE_SHA = 624c0a652de775dcdf9d641438b5c18ef4ce50d2`
- `HEAD = 259d6d68b59fe0cdca3d8d495371b84a226c67fa` (independently CI-qualified implementation revision)
- `TREE = 991817a776ae1b50e95b3969a7e6ed891294780b`
- `FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928`
- `HANDOFF_COMMIT = SELF` (the branch tip containing this handoff and the materialized gate is reported by the coordinating work chat)

## Files changed

- `.github/workflows/ws12-failure-semantics.yml`
- `research/greenfield-qualification/failure-semantics/**`
- `research/greenfield-qualification/FAILURE_SEMANTICS_GATE.json`
- `research/greenfield-qualification/FAILURE_SEMANTICS_GATE.md`
- `research/greenfield-qualification/WS12_HANDOFF.md`

No canonical integration-owned file, WS11 actual-card file, or WS01–WS09 historical evidence was modified.

## Outcome schema and category matrix

- `OUTCOME_SCHEMA = commander-simulator-next.failure-outcome.v1`
- Authoritative source: `failure-semantics/outcome-contract.schema.json`
- The Forge enum is generated from that source; it is not an independently maintained taxonomy.
- Required categories defined and executed: `16/16`.
- Category matrix: `SUCCESS`, `PLAYER_CANCELLED`, `ACTION_NOT_COMPLETABLE`, `ILLEGAL_RESPONSE`, `MALFORMED_RESPONSE`, `STALE_RESPONSE`, `WRONG_ACTOR`, `TIMEOUT`, `UNSUPPORTED_DECISION_PATH`, `UNSUPPORTED_RULES_PATH`, `ENGINE_FAILURE`, `TRANSPORT_FAILURE`, `PROCESS_FAILURE`, `REPLAY_DIVERGENCE`, `HIDDEN_INFO_VIOLATION`, `CARD_BEHAVIOR_FAILURE` all `PASS`.
- Existing WS01 decision errors mapped exhaustively: `12/12`.
- Every non-success category preserves the canonical pre-state hash and applies no selected-option fallback.
- Public payloads contain fixed category messages only; private exception detail and hidden card markers are excluded.
- `PROCESS_FAILURE` witness uses two OS child processes: one injected exit and one independently completed game-state transition; cross-game corruption is `false`.

## Tests

- Local Python contract suite: `5/5 PASS`.
- Local exact-pin Forge reactor: `mvn -B -DskipTests -pl forge-gui -am test-compile` — `BUILD SUCCESS`.
- Retained Q1 exact-pin validator: `JAVA_EXTERNAL_DECISION_CONTRACT=PASS`.
- WS12 exact-pin Java outcome contract: `WS12_JAVA_FAILURE_SEMANTICS=PASS`.
- CI workflow: all steps `PASS`, including overlay application, Forge compilation, both Java contracts, 16 machine-readable witnesses, gate adjudication, and evidence hashing.

## Immutable remote evidence

- `RUN_IDS = [33251299823]`
- `JOB_IDS = [99097321873]`
- `ARTIFACT_IDS = [9714458386]`
- `ARTIFACT_DIGESTS = [sha256:1ab90f946bc6c3943f5579fb014ff3aaef83daf15971067770e2d0485f0b9477]`
- CI gate SHA-256 inside the artifact: `15eee9b464a79260579d68dfd336c9db43997877d87a1df54aa27a6bdc3b88da`
- CI exact-pin compile log SHA-256: `d2aba65bea2fcabfbb0915d43c91d696c97838d94b09ba02bbbb15e7cd1d3862`
- CI Q1 validator log SHA-256: `8dd0d902f8990461be56403bec1044bd2f7c9dd51cfd36685b3efe8ce5703cdc`
- CI WS12 Java contract log SHA-256: `f6cab5e3dad960506139ce09eb4b3ac859b4a4e1a58da20f754ba91d34ba5c53`

## Evidence classes

- `DIRECTLY_VERIFIED`: exact base/pin, generated overlay presence, compile, Java contracts, category outputs, state hashes, OS process exits, artifact metadata.
- `CODE_DERIVED`: exhaustive WS01 error mapping, schema/enum identity, no-fallback and commit-policy assertions.
- `TECHNICALLY_CONFORMANT`: success/cancel and strict decision-response categories executed against the exact-pin overlay.
- `SYNTHETIC`: injected action/rules/engine/transport/process/replay/hidden-info/card-behavior fault witnesses. These prove category and failure behavior, not underlying card/rules correctness.

## Regression decisions

| Retained gate | Decision | Reason and result |
|---|---|---|
| Q1 strict decision boundary | `RERUN_NOW` | Unified mapping touches the exact-pin decision event outcome surface. Existing validator and exhaustive mapper both passed. |
| Q2 principal hidden information | `RERUN_NOW` | Public failure envelopes are a new principal-facing surface. All 16 payload witnesses excluded private markers and arbitrary exception details. |
| Q3 semantic replay | `RERUN_NOW` | `REPLAY_DIVERGENCE` is newly authoritative. Focused witness proved it is distinct and non-mutating; no replay engine path changed. |
| Q4 process isolation | `RERUN_NOW` | `PROCESS_FAILURE` is newly authoritative. Independent child-process fault/completion witness passed with zero cross-game corruption. |
| Q5 Commander/multiplayer | `NO_RERUN` | No Commander or multiplayer rules path changed. |

## Adjudication

- `FAILURE_SEMANTICS = PASS`
- `production_reachable_untyped_failure_outcomes = 0`
- `production_reachable_fallback_failure_handling = 0`
- Technical failure to pass/cancel/default/random/first-option/silent-skip coercions: `0`.
- Unsupported decision paths and unsupported rules paths fail closed as separate typed outcomes.
- Replay, hidden-information, card-behavior, transport, process, and engine failures remain distinct.

`BLOCKERS = []`

`NEXT_ACTION = Independently verify this branch head/tree, ownership, schema-generated Forge overlay, CI artifact and gate. Do not integrate or begin architecture freeze unless WS11 also independently passes and a later integration workstream adjudicates both successors.`
