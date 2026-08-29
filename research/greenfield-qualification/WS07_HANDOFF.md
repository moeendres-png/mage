# WS07 — Rules / Commander Multiplayer Conformance — Abschluss-Handoff

## Status

- `WORKSTREAM_COMPLETE=TRUE`
- `Q5_COMMANDER_MULTIPLAYER=PASS`
- Evidence class: `TECHNICALLY_CONFORMANT`
- Qualification status: `PASS`

This handoff records the completed WS07 qualification. It does not broaden the evidence class to `EXTERNALLY_RULE_VALIDATED` and does not claim total Magic card/rules coverage beyond the defined WS07 scenario matrices.

## Audited boundary

- Repository: `moeendres-png/mage`
- Workstream branch: `work/ws07-commander-conformance-20260828`
- `AUDIT_BASE_SHA`: `c0e42fb42c4a603aff4a76b1284f8271c12bfd42`
- Qualified source HEAD: `87834da73f22e62a1803733be812d3b22b9f485b`
- Qualified source tree: `f2605ec49015b5d03bf92e4456ed76579fa08799`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

The qualified source HEAD above is the immutable semantic qualification reference. This handoff commit is administrative only and is intentionally outside the WS07 workflow path filter; it does not replace the qualified source identity.

## Final qualification evidence

- Workflow run: `33244368567`
- Job: `99079149450`
- Artifact ID: `9712369379`
- Artifact name: `ws07-commander-conformance-33244368567`
- Artifact digest: `sha256:72d2f8af3ed4e9892451546132dd7e09e33400f728983f6f0e9be341540b2c5e`
- Test exit code: `0`
- Collector exit code: `0`
- Surefire: `Tests run: 11, Failures: 0, Errors: 0, Skipped: 0`

Artifact evidence includes:

- `EXECUTION.json`
- `WS07_CONFORMANCE.json`
- `RULES_MATRIX_A_T.executed.json`
- `RULES_MATRIX_C01_C22.executed.json`
- `raw-semantic.jsonl`
- Maven log and Surefire reports

## Gates

- A–T defined: `20`
- A–T semantic 4P PASS: `20/20`
- C01–C22 defined: `22`
- C01–C22 semantic 4P PASS: `22/22`
- Authoritative rows PASS: `42/42`
- `all_42_authoritative_rows_semantic=PASS`
- `all_mandatory_4P_commander_scenarios=PASS`
- `2P_conformance_required_subset=PASS`
- `3P_conformance_required_subset=PASS`
- `4P_conformance_required_subset=PASS`
- `5P_conformance_required_subset=PASS`
- `Q5_COMMANDER_MULTIPLAYER=PASS`
- Exact Forge pin match: `true`
- Process-exit-only semantic passes: `0`
- Raw semantic row errors: `0`
- Invented IDs/tests: `0`
- Forbidden unrecovered regression mentions: `0`
- Duplicate raw semantic IDs: `0`

## Qualified semantic scope

The executable evidence covers the WS07 A–T rules categories and C01–C22 Commander/multiplayer scenarios, including 4P Commander initialization, command-zone casting and tax behavior, commander zone movement choices, commander-damage identity and threshold behavior, APNAP, multiplayer combat, player elimination/leaves-game consequences, explicit discretionary Commander choices, deterministic non-RNG replay checks, and required 2P–5P technical subsets.

## Evidence boundary

`TECHNICALLY_CONFORMANT` means the defined WS07 semantic scenarios passed against the exact pinned Forge runtime through engine-state assertions. It does **not** by itself establish:

- complete official-Magic-rules validation for every reachable game state;
- complete actual-card behavioral coverage;
- Oracle-wide behavioral completeness;
- replacement for WS09 official-rules differential adjudication or WS10 actual-card behavior coverage.

Those remain separate workstream responsibilities.

## Integration handoff

For downstream integration/orchestration, consume:

1. qualified source HEAD `87834da73f22e62a1803733be812d3b22b9f485b`;
2. Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`;
3. run `33244368567` / artifact `9712369379` as the canonical WS07 semantic evidence bundle;
4. `WS07_CONFORMANCE.json` as the fail-closed gate result.

No further WS07 requalification is required unless the qualified source, Forge pin, scenario contract, collector contract, or integration-relevant dependency changes.
