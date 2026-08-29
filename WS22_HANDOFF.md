# WS22 — Actual-Path Failure Adapters: Replay + Hidden Information

## Scope

This workstream closes exactly the WS12 production bindings for:

- `REPLAY_DIVERGENCE`
- `HIDDEN_INFO_VIOLATION`

It does not modify the shared WS12 outcome schema or the shared WS12 gate and does not adjudicate overall `FAILURE_SEMANTICS`.

## Frozen inputs

- Base: `80743bdbc2950b00e422f3deb38f04111f30a4d4`
- WS05: `554bb06af0dd5e542ff8bbfd5e96054a74642d3a` (read-only)
- WS06: `e23af2b621f2e318014491b8a84146ed4ad3bed6` (read-only)
- WS90 integrated runtime: `55820618e7243bd5ba8cfa33c3148cea8c166c73` (read-only)
- Forge: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Qualified WS05 run/artifact: `33210994482` / `9701653278`
- Qualified WS06 run/artifact: `33209213338` / `9701086657`

## Actual detector bindings

### REPLAY_DIVERGENCE

The adapter imports and executes the exact `semantic_replay.compare` implementation from the read-only WS06 dependency. The immutable qualified A/B/C evidence is first required to compare `PASS` with zero semantic, RNG, and decision divergences. A test-only copy of process B then receives one controlled canonical semantic-state field at checkpoint 1. The exact comparator must return `FAIL`, preserve a structural first divergence, emit `E_SEMANTIC_DIVERGENCE`, report at least one semantic-state divergence, report zero RNG/decision divergence, and continue to state `stdout_used_as_replay_criterion=false`.

The public failure is bound to WS12 `REPLAY_DIVERGENCE` with `state_committed=false`. Expected/actual divergent semantic values are not copied into the external failure envelope or WS22 adapter trace.

### HIDDEN_INFO_VIOLATION

The adapter uses the exact qualified WS05 probe read-only and adds a test-workspace-only entry point that calls WS05's existing private `authorized(CardView, PlayerView)` and `identityBearing(CardView)` logic and increments the same `transportLeaks` detector counter.

The 4-player Commander negative-path test obtains a real hidden library `Card`, its real `CardView`, and Bob's real `PlayerView` from the live hosted game. It proves that the datum is identity-bearing and unauthorized for Bob, requires the qualified Q2 detector baseline to be zero, injects that concrete cross-principal datum, and requires the detector to move from exactly 0 to exactly 1 leak. The immediate authoritative game-state witness is unchanged across detection. It then emits WS12 `HIDDEN_INFO_VIOLATION`, verifies the public envelope contains neither the secret card name nor its SHA-256 digest, and aborts the current decision/game before any response can be returned. No pass/cancel/first/random/default fallback is possible.

## Regression classification

- Q2 hidden information: `NO_RERUN`. WS22 does not modify the qualified WS05 source or production visibility overlay. The only WS05 extension is applied to a copied probe in the CI test workspace, and the focused negative test exercises the existing Q2 authorization detector.
- Q3 semantic replay: `NO_RERUN`. WS22 does not modify the qualified WS06 comparator, tape contract, RNG overlay, or replay runtime. It first revalidates the immutable qualified A/B/C artifact through the exact comparator and mutates only a copied evidence record for the negative probe.

If either actual qualified path changes in later integration, this no-rerun classification is invalid and targeted Q2/Q3 requalification is required.

## Machine-readable evidence

The WS22 workflow emits and hashes:

- `REPLAY_DIVERGENCE_TRACE.json`
- `HIDDEN_INFO_VIOLATION_RUNTIME.json`
- `HIDDEN_INFO_VIOLATION_TRACE.json`
- `WS22_FAILURE_REPLAY_HIDDEN_GATE.json`
- provenance, compile/runtime logs, exact dependency metadata, and `hashes.sha256`

## Completion rule

`WORKSTREAM_COMPLETE=TRUE` is permitted only when the branch workflow succeeds and the final gate simultaneously reports:

- `REPLAY_DIVERGENCE=PASS`
- `HIDDEN_INFO_VIOLATION=PASS`
- every WS22 hard gate `true`
- `shared_ws12_schema_or_gate_modified=false`

Overall `FAILURE_SEMANTICS` remains `DEFERRED_TO_LATER_INTEGRATION`.

## Final live evidence

This section is updated after the WS22 workflow has run and its artifact has been directly inspected.
