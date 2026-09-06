# WS33 ABC — A-rest Direct31 runtime v5 run 34058130790 — terminal FAIL

Status: **FAIL_CLOSED**
Classification: **DIRECTLY_VERIFIED runtime PASS + CODE_DERIVED evidence-verifier defect**
Forge Rules Core defect: **NOT PROVEN**
Coverage promotion: **FALSE**
Coverage mutated during witness: **FALSE**

## Frozen lineage

- source HEAD: `23d16c74cc5ec853f17896369ac6ce86443e5391`
- source TREE: `5928fa3ba2bcd9bc9404d3faf025b9558732dbe2`
- run: `34058130790`
- job: `101553684254`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- topology artifact: `9980023181`
- runtime artifact: `9996679441`
- runtime artifact digest: `sha256:7ed54f2cea88e086265db9abbb9c3c3620d46dc2f75a00dc2185262b9af2dbf0`
- downloaded ZIP SHA-256 independently matched the GitHub digest exactly.

## Runtime result

The v5 MANA_PAYMENT cancellation normalization closed the prior three CostPayment failures.

`DIRECT31_RECORD_GATE.json`:
- status `PASS`
- exact paths `31`
- failures `0`
- coverage mutated `false`

`DIRECT31_RUNTIME_GATE.json`:
- status `PASS`
- exact paths `31`
- spells `24`
- activated abilities `7`
- decision-required `31`
- RNG-required `2`
- hidden-required `31`
- replay-required `31`
- actual-card source-bound `true`
- PlaySpellAbility authoritative `true`
- manual target injection `false`
- direct effect resolution `false`
- semantic replay equal `true`
- failures `0`
- coverage mutated `false`

Thus Record and fresh Replay both completed all 31 actual-card paths successfully, including stack/source-root reachability and CostPayment through Forge.

## Sole terminal gate failure

`DIRECT31_PRINCIPAL_OBSERVATION_GATE.json` is `FAIL_CLOSED` with exactly one failure:

`record_replay_observation_multiset_mismatch`

Both runs independently contain:
- observation events: `1964`
- `SERVER_GRANT`: `491`
- `CLIENT_VISIBLE`: `491`
- `SERVER_REVOKE`: `491`
- `CLIENT_HIDDEN`: `491`
- observed path count: `4`
- runtime hidden leak deltas: `0`
- cross-principal leak deltas: `0`

Independent artifact adjudication shows:

1. server-side normalized tuples `(path, kind, principal_id, card_id, decision_kind, identity_match)` are exactly equal between Record and Replay;
2. client-side semantic tuples `(path, kind, principal_id, card_id, identity_match)` are exactly equal between Record and Replay;
3. every per-card lifecycle remains strict `SERVER_GRANT -> CLIENT_VISIBLE -> SERVER_REVOKE -> CLIENT_HIDDEN` and closes back to hidden;
4. the only raw multiset difference is the client event `decision_kind` field, whose values are transport metadata such as `delta:67` in Record versus `delta:66` in Replay (and analogous delta offsets on the second affected path).

The current verifier normalizes `decision_kind` for **all** observation kinds. That is semantically correct for `SERVER_GRANT/SERVER_REVOKE`, where it records the Forge observation/decision reason, but incorrect for `CLIENT_VISIBLE/CLIENT_HIDDEN`, where the field carries a transport delta sequence label rather than a rules/observation semantic identity.

Affected raw-comparison paths are only:
- `forge-behavior-v2:c71091504723b8775c2cefbf39385fb866874ad1` — Demolition Field
- `forge-behavior-v2:e6d054082bcc52f9eef03f3092279319d865eb3a` — Chaos Warp

No card identity, principal identity, visibility transition, server grant/revoke reason, path attribution, event count, or semantic game state differs.

## Repair boundary

Repair only the evidence comparator:
- retain `decision_kind` in normalized server events;
- ignore client transport `delta:<n>` metadata when comparing Record/Replay semantic observation equality;
- retain exact path/kind/principal/card/identity equality for client events;
- retain strict lifecycle validation independently for both Record and Replay;
- retain zero-leak requirements.

Do not alter Forge runtime, visibility grants, transport behavior, pilot choices, target/cost/mana logic, RNG, or coverage.

A fresh run is required after the verifier repair; this failed run is not promotable evidence despite its green runtime sub-gates.
