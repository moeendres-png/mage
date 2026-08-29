# WS24 — Q6 Semantic Integration — Handoff

## Scope

WS24 is the first workstream allowed to integrate the five WS14 owner-family witness shards into a successor witness registry and reclassify all `1678` exact Oracle identities. It consumes WS15–WS19 read-only and does not rerun their already-qualified engine suites.

## Fixed base

- Repository: `moeendres-png/mage`
- Branch: `work/ws24-q6-semantic-integration-20260829`
- Base / WS14 final HEAD: `d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5`
- WS14 base tree: `5725f47951938bc71af181cf1617e6b3be158804`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Integration semantics

The integrator independently checks the immutable WS14 manifest/per-identity/unresolved hashes, verifies that the five shards account for exactly the closed `174`-primitive owner partition, and requires every integrated `PASS` primitive to have an actual WS14-ABI witness with `execution=PASS`, `stdout_only=false`, and an immutable 64-hex trace hash.

For every Oracle identity, the exact WS14 identity object is embedded unchanged inside the WS24 classification row so source paths, source byte hashes and WS11 full-script signature IDs remain preserved. Classification is fail-closed:

- any ambiguous source binding or unresolved WS14 binding => `UNKNOWN`;
- any `UNSUPPORTED` primitive => `UNSUPPORTED`;
- otherwise any `UNKNOWN` primitive => `UNKNOWN`;
- otherwise any `PARTIAL` primitive => `PARTIAL`;
- only an unambiguous identity with zero unresolved bindings and all resolved primitives `PASS` may become `CONDITIONAL_FULL`;
- no identity is promoted to `FULL` by parsing, source presence, or global Q2/Q3 inheritance.

The gate may report `WORKSTREAM_COMPLETE=TRUE` while keeping `Q6_ACTUAL_CARD_BEHAVIOR=FAIL_CLOSED`; workstream completion means the integration/adjudication is complete, not that the candidate has passed Q6.

## Expected fail-closed frontier before execution

The already-qualified shard results imply at least:

- WS15: `0 PASS / 76 PARTIAL`
- WS16: `2 PASS / 51 PARTIAL`
- WS17: `11 PASS / 10 PARTIAL`
- WS18: `0 PASS / 10 PARTIAL`
- WS19: `0 PASS / 14 PARTIAL`

That is `13 PASS / 161 PARTIAL` across `174` primitives, before considering WS14's `1800` explicit unresolved bindings. WS24 must not promote Q6 unless new actual evidence legitimately changes those inputs; this integration does not create such evidence.

## Outputs

The dedicated workflow must emit and hash:

- `WS24_WITNESS_REGISTRY.json`
- `WS24_PER_IDENTITY.jsonl`
- `WS24_UNPROVED_PRIMITIVES.json`
- `WS24_UNRESOLVED_BINDINGS.jsonl`
- `Q6_ACTUAL_CARD_BEHAVIOR_GATE.json`
- `WS24_HASHES.sha256`

## Final live evidence

Pending the dedicated WS24 integration run.
