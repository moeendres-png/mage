# WS21 — Actual-Path Failure Adapters: Engine + Transport — Handoff

WORKSTREAM_COMPLETE=TRUE
ENGINE_FAILURE=PASS
TRANSPORT_FAILURE=PASS
FAILURE_SEMANTICS_PROMOTED=FALSE

## Scope

WS21 closes exactly the WS12 production-binding gaps `ENGINE_FAILURE` and `TRANSPORT_FAILURE` against the candidate process-per-game topology. It does not adjudicate or promote the other WS12 categories and does not promote the aggregate `FAILURE_SEMANTICS` gate.

## Immutable inputs

- Repository: `moeendres-png/mage`
- Branch: `work/ws21-failure-engine-transport-20260829`
- AUDIT_BASE_SHA: `80743bdbc2950b00e422f3deb38f04111f30a4d4`
- AUDIT_BASE_TREE: `9a2a52932a0d69dcf06c2392cddcf40b47e810cc`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Qualified source revision

The executable qualification ran against:

- QUALIFIED_HEAD: `cfd9ca96a796a825b0c70d7caff849ae49883752`
- QUALIFIED_TREE: `92fe7eab1d67b7b7dfa4c305c664cddd6f05c74e`

The later handoff-only commit changes documentation only and is intentionally not treated as a new executable qualification revision.

## Qualification run

- GitHub Actions run: `33254238155`
- Job: `qualify`
- Final conclusion: `success`
- Evidence artifact ID: `9715407935`
- Artifact name: `ws21-failure-engine-transport`
- Artifact SHA-256: `2b4456226526e941e87d4b8f0c0f54e3410635e6382ddef8e3812b98eefbec35`
- Internal `hashes.sha256`: verified successfully for every listed evidence file.

## Gate result

`WS21_ENGINE_TRANSPORT_GATE.json`:

- `status = PASS`
- `ENGINE_FAILURE = PASS`
- `TRANSPORT_FAILURE = PASS`
- `FAILURE_SEMANTICS = NOT_PROMOTED`
- `overall_promotion_performed = false`
- `process_model = ONE_GAME_PER_OS_PROCESS`

All hard gates are true:

- `DETERMINISTIC_MACHINE_READABLE_TRACES`
- `ENGINE_ACTUAL_PATH_TYPED`
- `ENGINE_DISTINCT_FROM_PROCESS_AND_CANCEL`
- `ENGINE_NO_FAILED_STATE_COMMIT`
- `ENGINE_NO_SILENT_CONTINUATION`
- `PROCESS_PER_GAME_TOPOLOGY_PRESERVED`
- `TRANSPORT_ACTUAL_PATH_TYPED`
- `TRANSPORT_DIAGNOSTIC_HIDDEN_INFO_LEAKS_ZERO`
- `TRANSPORT_DISTINCT_FROM_ENGINE_AND_PROCESS`
- `TRANSPORT_DISTINCT_FROM_MALFORMED_RESPONSE`
- `TRANSPORT_NO_FAILED_STATE_COMMIT`
- `TRANSPORT_NO_SUBSTITUTED_DECISION`

## ENGINE_FAILURE witness

Actual engine-side fault site:

`forge.game.GameAction.changeZone:entry`

Observed evidence:

- category: `ENGINE_FAILURE`
- worker PID: `2805`
- worker exit: `0`
- process alive while reporting: `true`
- engine fault fired: `true`
- original engine body reached after injected fault: `false`
- state committed: `false`
- decision opened / validated / applied: `1 / 1 / 1`
- transport boundary propagations: `0`

This distinguishes an engine execution failure from process termination and from decision transport failure. The controlled failure occurs before the first original statement at the bound engine site and does not silently continue.

## TRANSPORT_FAILURE witness

The transport witness uses the existing WS01 authoritative external-decision provider boundary rather than creating a second pilot/rules path. The controlled fault is a truncated response frame after request delivery, producing a decode-stage transport failure.

Observed evidence:

- category: `TRANSPORT_FAILURE`
- worker PID: `2953`
- worker exit: `0`
- process alive while reporting: `true`
- state committed: `false`
- decision opened / validated / applied: `1 / 0 / 0`
- transport boundary propagations: `1`
- transport stage: `DECODE_RESPONSE`
- requests written: `1`
- responses decoded: `0`

Therefore no response was validated or applied and no pass/cancel/default/random fallback was substituted.

## MALFORMED_RESPONSE negative control

A separate fully decodable but schema-invalid response proves transport loss is not being collapsed into malformed-response handling.

Observed evidence:

- category: `MALFORMED_RESPONSE`
- worker PID: `3076`
- worker exit: `0`
- state committed: `false`
- transport boundary propagations: `0`
- requests written: `1`
- responses decoded: `1`

Gate negative control:

- `category = MALFORMED_RESPONSE`
- `transport_failure_propagations = 0`

## Process isolation / topology

`processes.tsv` records three distinct worker PIDs:

- engine: `2805`
- transport: `2953`
- malformed-control: `3076`

`distinct_worker_pids = 3` and `games_per_worker_process = 1`. The gate therefore preserves the selected one-game-per-OS-process topology.

## Hidden-information / diagnostic safety

`diagnostic_hidden_info_leaks = 0`.

The machine-readable outcomes and fault traces contain only the qualified diagnostic fields and do not expose the private-card canary used by the witness.

## Regressions preserved

On the same qualified source revision and Forge pin:

- exact-pin combined compile: PASS
- Q1 external-decision contract regression: PASS
- WS12 unified outcome regression: PASS

No previously valid qualification step was rerun after the final runtime success because the only subsequent change is this handoff document.

## Evidence classification

- engine fault-site binding: `CODE_DERIVED`
- transport controller binding: `CODE_DERIVED`
- engine runtime witness: `TECHNICALLY_CONFORMANT`
- transport runtime witness: `TECHNICALLY_CONFORMANT`
- malformed-response negative control: `TECHNICALLY_CONFORMANT`
- diagnostic hidden-information scan: `DIRECTLY_VERIFIED`

## Integration contract

WS90 / the integration workstream may consume this branch as evidence that the two WS21-owned bindings are closed:

- `ENGINE_FAILURE = PASS`
- `TRANSPORT_FAILURE = PASS`

It must not infer from WS21 alone that the aggregate `FAILURE_SEMANTICS` qualification is complete. Aggregate promotion remains a separate cross-workstream decision after the remaining categories are independently bound and qualified.
