# WS12 unified failure semantics — fail-closed handoff

`WORKSTREAM_COMPLETE = TRUE_FAIL_CLOSED`

## Provenance

- `BRANCH = work/ws12-failure-semantics-20260829`
- `BASE_SHA = 624c0a652de775dcdf9d641438b5c18ef4ce50d2`
- `HEAD = 9566758b0d7b7cd5b1cf9847f0e438b67025c403` (CI-qualified implementation and fail-closed gate revision)
- `TREE = e7a71586ab52bd24ebe5b6b7b51bf8f6099729a1`
- `FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928`
- `HANDOFF_COMMIT = SELF`; the final branch tip containing this materialized handoff is reported externally because a commit cannot contain its own hash.

## Ownership

Changed only:

- `.github/workflows/ws12-failure-semantics.yml`
- `research/greenfield-qualification/failure-semantics/**`
- `research/greenfield-qualification/FAILURE_SEMANTICS_GATE.json`
- `research/greenfield-qualification/FAILURE_SEMANTICS_GATE.md`
- `research/greenfield-qualification/WS12_HANDOFF.md`

No canonical integration-owned file, WS11 actual-card file, or WS01–WS09 historical evidence was modified.

## Outcome schema and honest category matrix

- `OUTCOME_SCHEMA = commander-simulator-next.failure-outcome.v1`
- Required categories defined: `16/16`.
- Exact-pin decision-tape/mapper bindings: `SUCCESS`, `PLAYER_CANCELLED`, `ILLEGAL_RESPONSE`, `MALFORMED_RESPONSE`, `STALE_RESPONSE`, `WRONG_ACTOR`, `TIMEOUT`, `UNSUPPORTED_DECISION_PATH` — `PASS` for the scoped contract.
- OS process-supervisor witness: `PROCESS_FAILURE` — `CONDITIONAL_PASS` for process fault isolation.
- Generic construction witnesses without production capture: `ACTION_NOT_COMPLETABLE`, `UNSUPPORTED_RULES_PATH`, `ENGINE_FAILURE`, `TRANSPORT_FAILURE`, `REPLAY_DIVERGENCE`, `HIDDEN_INFO_VIOLATION`, `CARD_BEHAVIOR_FAILURE` — `PARTIAL`.

The seven `PARTIAL` witnesses prove only that the authoritative enum can represent the category and that the synthetic harness does not mutate its model state. They do **not** prove that an actual engine, transport, rules, replay, hidden-information, or card-behavior failure is detected, captured, and emitted without fallback on the candidate runtime path.

## Tests and workflow evidence

- Local Python fail-closed contract suite: `5/5 PASS`.
- Exact-pin Forge reactor: `mvn -B -DskipTests -pl forge-gui -am test-compile` — `BUILD SUCCESS`.
- Retained Q1 exact-pin validator focused probe: `JAVA_EXTERNAL_DECISION_CONTRACT=PASS`.
- WS12 exact-pin Java vocabulary/decision-mapper probe: `WS12_JAVA_FAILURE_SEMANTICS=PASS`.
- CI correctly accepts only qualifier exit `1` plus `FAIL_INCOMPLETE`, `status=FAIL`, seven exact unbound categories, and `UNKNOWN` production metrics. This green workflow verifies fail-closed adjudication; it is not a FAILURE_SEMANTICS PASS.

## Remote evidence

- All `RUN_IDS = [33251299823, 33251524952, 33251601240, 33251764260]`
- All `JOB_IDS = [99097321873, 99097913910, 99098113793, 99098539742]`
- All `ARTIFACT_IDS = [9714458386, 9714520021, 9714545905, 9714593341]`
- All `ARTIFACT_DIGESTS = [sha256:1ab90f946bc6c3943f5579fb014ff3aaef83daf15971067770e2d0485f0b9477, sha256:552e585f270e6766216d81512805f8ffc752667a4b553b2d719c484181e5d605, sha256:bb45fd18afacf5ff80eb3c3fed169b824e57181e467244b8445327b0a3b9f0ef, sha256:c1839345757a1fb80c553f9b16078b09a1a2b3bab25e30fbc7bc659bc0404073]`
- Superseding run/job/artifact: `33251764260` / `99098539742` / `9714593341`.
- Superseding CI gate SHA-256: `68ff352883404af70651549fcf37ec9bb6dd665b8e16bc7b8807e2eadfcebc15`
- Superseding CI compile log SHA-256: `b060b0b668a768a897512e661bde211a2180332808f1a1edf0232404dc639ef8`
- CI Q1 focused validator log SHA-256: `8dd0d902f8990461be56403bec1044bd2f7c9dd51cfd36685b3efe8ce5703cdc`
- CI WS12 Java probe log SHA-256: `f6cab5e3dad960506139ce09eb4b3ac859b4a4e1a58da20f754ba91d34ba5c53`
- Run `33251299823` is superseded and rejected because it emitted the over-broad PASS.
- Run `33251524952` correctly generated fail-closed evidence but the job failed before asserting the expected qualifier exit; it is diagnostic only.
- Run `33251601240` is valid fail-closed evidence but is superseded by the presentation-corrected `33251764260` artifact.

## Evidence classes

- `DIRECTLY_VERIFIED`: exact base/pin, overlay application, Forge compile, strict decision mapping, category construction, OS process exits, artifact metadata.
- `CODE_DERIVED`: exhaustive WS01 decision-error mapping and schema-generated enum identity.
- `TECHNICALLY_CONFORMANT`: scoped strict decision-response outcome mapping only.
- `SYNTHETIC`: the seven unbound generic fault constructions; not production behavior evidence.
- `UNKNOWN`: actual production capture and no-fallback behavior for the seven unbound categories.

## Regression decisions

| Retained gate | Decision | What actually ran |
|---|---|---|
| Q1 strict decision boundary | `NO_RERUN` | Additive classification did not change validation. Exact-pin validator focused probe passed; the full predecessor gate was not rerun. |
| Q2 principal hidden information | `AUDIT_NEEDS_RERUN` | Fixed constructed payloads were marker-checked, but unbound actual payloads remain unknown. This was not a full Q2 rerun. |
| Q3 semantic replay | `AUDIT_NEEDS_RERUN` | Only outcome construction/non-mutation was probed; no replay divergence detector is bound. This was not a full Q3 rerun. |
| Q4 process isolation | `NO_RERUN` | Focused two-child process fault witness passed. No process-isolation implementation changed; the full predecessor gate was not rerun. |
| Q5 Commander/multiplayer | `NO_RERUN` | No Commander or multiplayer rules path changed. |

## Fail-closed adjudication

- `FAILURE_SEMANTICS = FAIL_INCOMPLETE`
- `production_reachable_untyped_failure_outcomes = UNKNOWN` (not proven `0`)
- `production_reachable_fallback_failure_handling = UNKNOWN` (not proven `0`)
- Contract-witness untyped outcomes: `0`; this is not promoted to the production metric.
- Contract-witness fallback handling: `0`; this is not promoted to the production metric.

## Blockers

Exactly seven production-facing detection/capture adapters and exact-path fault-injection witnesses are missing:

1. `ACTION_NOT_COMPLETABLE`
2. `UNSUPPORTED_RULES_PATH`
3. `ENGINE_FAILURE`
4. `TRANSPORT_FAILURE`
5. `REPLAY_DIVERGENCE`
6. `HIDDEN_INFO_VIOLATION`
7. `CARD_BEHAVIOR_FAILURE`

For each, the successor must bind the actual candidate runtime boundary, inject or induce the real failure, assert the exact typed outcome, prove prohibited state mutation/fallback is absent, and verify the emitted payload. Enum construction or stdout-only tokens remain insufficient.

`NEXT_ACTION = Stop WS13 and architecture-freeze progression. Implement the seven actual-path adapters only after the candidate production topology identifies their owning runtime boundaries, then rerun this gate and only the predecessor audits whose real paths changed.`
