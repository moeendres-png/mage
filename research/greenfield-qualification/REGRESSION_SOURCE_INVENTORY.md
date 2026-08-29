# REGRESSION SOURCE INVENTORY

## Scope

Historical test-definition provenance only for the four requested named regressions. Audit base: `c0e42fb42c4a603aff4a76b1284f8271c12bfd42` / tree `fb06c61dd87b4b742722925cd7374d8f037e1f47`.

No rules campaign was run. No card behavior was qualified. Missing semantics were not reconstructed from card names, prior chat memory, or expected historical behavior.

## Authoritative retained source

`research/greenfield-qualification/scenarios.json` contains the four names as a `regressions` array.

- definition origin commit: `0af75ca2593b3f81c320095d2279678756ff663c`
- definition origin blob: `7b9d0a55a0b5838cf6db588e51876b917eb1ecf5`
- manifest blob at audit base: `55284819ab042aa7ad5e80a533d91c50f4f88694`

Neither the origin manifest nor the audit-base manifest contains semantic preconditions, an action/decision sequence, or an expected semantic outcome for these names.

## Named regressions

| ID | Name | Manifest identifier | Source identifier | Exact definition | Evidence |
|---|---|---|---|---|---|
| R01 | Hedron Archive | `HEDRON_ARCHIVE` | `scenarios.json#/regressions/0` | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| R02 | Glissa Sunslayer | `GLISSA_SUNSLAYER` | `scenarios.json#/regressions/1` | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| R03 | Slip Out the Back | `SLIP_OUT_THE_BACK` | `scenarios.json#/regressions/2` | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| R04 | Void Rend | `VOID_REND` | `scenarios.json#/regressions/3` | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |

For every row:

- requirement/name source: `AVAILABLE`;
- `semantic_precondition = null`;
- `action_decision_sequence = null`;
- `expected_semantic_outcome = null`;
- semantic evidence class: `UNKNOWN`;
- no expected result is inferred from the card name.

The full source SHA/blob tuple for every row is recorded in `REGRESSION_SOURCE_INVENTORY.json`.

## Historical/source search

| Source | Result | Evidence |
|---|---|---|
| Live Greenfield manifest at audit base | Four names present; no machine-readable semantic body | DIRECTLY_VERIFIED |
| Manifest origin commit `0af75ca...` | Same four names; no machine-readable semantic body | DIRECTLY_VERIFIED |
| Exact commit-message searches for `HEDRON_ARCHIVE`, `GLISSA_SUNSLAYER`, `SLIP_OUT_THE_BACK`, `VOID_REND` | No matches | DIRECTLY_VERIFIED, scoped to commit-message search only |
| `research/commander-playtest-lab` at audit base | Path not present | DIRECTLY_VERIFIED, scoped to audit-base tree |
| `.github/workflows/greenfield-xmage-targeted.yml` blob `aadfc7862635d9b7fe5157bf91fcc6839d972184` | Targeted XMage/Commander qualification logic exists, but no exact semantic definition for the four names | DIRECTLY_VERIFIED |
| Retained GitHub Actions run/artifact lookup | No usable retained payload tying a named regression to an exact machine-readable definition was resolved | UNKNOWN; no global absence claim |

The Actions lookup did **not** trigger a new workflow and does not justify asserting that no historical artifact ever existed. It only means no qualifying retained artifact definition was obtained in this audit.

## Newly discovered regressions

No additional complete machine-readable regression definition was discovered in the audited sources.

`newly_discovered_complete_regression_definition_count = 0`

## Gates

| Gate | Result |
|---|---|
| `named_regression_inventory_count = 4` | PASS |
| `named_regression_inventory_complete = true` | PASS |
| `unproven_invented_definitions = 0` | PASS |
| all missing definitions classified `SOURCE_DEFINITION_UNAVAILABLE` | PASS |

Production qualification remains `NOT_RUN`.

## WS07 boundary

The four names are authoritative regression *identifiers*, not executable scenario authority. WS07 must fail closed rather than manufacture setup, decision tape, or expected outcomes. If an exact historical definition is recovered later, it should be attached with its original SHA/artifact provenance and re-audited before use.
