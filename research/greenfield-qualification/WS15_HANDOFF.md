# WS15 — Action / Cost / Mana / Target / Mode / Decision Witnesses

`WORKSTREAM_COMPLETE: true` (fail-closed handoff; Q6 is not promoted)

- `BRANCH`: `work/ws15-witness-action-cost-decision-20260829`
- `BASE_SHA`: `d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5`
- `BASE_TREE`: `5725f47951938bc71af181cf1617e6b3be158804`
- `FORGE_PIN`: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- `OWNER_FAMILY`: `ACTION_COST_DECISION`
- `OWNED_PRIMITIVES`: `76`
- `PASS`: `0`
- `PARTIAL`: `76`
- `UNKNOWN`: `0`
- `UNSUPPORTED`: `0`
- `DEDICATED_SCENARIO_COUNT`: `0`
- `CARD_NAME_PRODUCTION_HACKS`: `0`
- `Q6_ACTUAL_CARD_BEHAVIOR`: `FAIL`

## Evidence

`witness-shards/action-cost-decision/ws15_materialize.py` deterministically
materializes one row per exact WS14-assigned primitive.  It does **not** convert
dispatch provenance, successful source checkout, loadability, or global gate
status into behavior proof.  Every row is explicitly `PARTIAL` and names the
missing proof: an actual-card pinned-Forge execution through a legal,
authoritatively supplied decision path with state assertions and a trace.

The workflow verifies the WS14 base/tree and exact Forge pin, materializes the
machine-readable artifact and publishes its SHA-256. `RUN_IDS`, `JOB_IDS`,
`ARTIFACT_IDS`, and `ARTIFACT_DIGESTS` must be filled only from the completed
workflow run; no synthetic identifiers are recorded here.

## Tests

- `python3 actual-card-behavior/witness-shards/action-cost-decision/test_ws15_contract.py`
- `.github/workflows/ws15-witness-action-cost-decision.yml`

## Evidence classes

- dispatch binding: `CODE_DERIVED`
- semantic behavior: `UNKNOWN` / explicit non-PASS (no execution inferred)

## Blocker / next action

The smallest blocker is a pinned-Forge external-pilot semantic harness that
can obtain and answer real authoritative `DecisionRequest`s without a test
driver recreating decision legality. Build that harness first, then add a
state-asserting ABI witness per exercised primitive; leave all other rows
non-PASS until independently executed.
