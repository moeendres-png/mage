# TEST CORPUS SOURCE AUDIT

## Scope and authority

This artifact audits **test-definition provenance only** at `AUDIT_BASE_SHA=c0e42fb42c4a603aff4a76b1284f8271c12bfd42` (`tree=fb06c61dd87b4b742722925cd7374d8f037e1f47`). No rules campaign or semantic qualification was run and no expected outcome was reconstructed from a requirement label.

The authoritative requirement manifest is `research/greenfield-qualification/scenarios.json`:

- definition origin: `0af75ca2593b3f81c320095d2279678756ff663c`
- origin blob: `7b9d0a55a0b5838cf6db588e51876b917eb1ecf5`
- blob at audit base: `55284819ab042aa7ad5e80a533d91c50f4f88694`

Read-only derived sources:

- `RULES_MATRIX_A_T.json` blob `9dd4bbc65614ca5c477737f5b67a5b3cf7484b53`
- `RULES_MATRIX_C01_C22.json` blob `4719688db82d45c99da18ebd84478425a8c8a6a6`
- `materialize_matrices.py` blob `dfb28de5c8e96a389ad8a71126ba35a3c63c46ff`

`materialize_matrices.py` copies labels from the manifest, enforces the 20/22 counts, and keeps qualification `NOT_RUN`. It does not provide semantic setup, action/decision sequences, or expected semantic outcomes. Therefore a label, and for C01-C22 the metadata value `AVAILABLE_IN_SCENARIO_MANIFEST`, establishes requirement provenance only. It does **not** establish an executable scenario definition.

The machine-readable companion `TEST_CORPUS_SOURCE_AUDIT.json` contains the source identifier and source SHA/blob for every item plus explicit `null` semantic fields. All missing exact definitions are classified `SOURCE_DEFINITION_UNAVAILABLE`.

## A-T inventory

| ID | Requirement definition | Requirement source | Exact semantic definition | Evidence |
|---|---|---|---|---|
| A | `basic_turn_progression` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| B | `land_play` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C | `mana_activation` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| D | `casting_and_costs` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| E | `stack_and_priority` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| F | `targets` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| G | `triggers` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| H | `replacement_effects` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| I | `state_based_actions` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| J | `combat` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| K | `commander_rules` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| L | `multiplayer` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| M | `hidden_information` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| N | `search_and_shuffle` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| O | `alternate_and_additional_costs` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| P | `continuous_effects_and_layers` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| Q | `copy_and_object_identity` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| R | `player_elimination` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| S | `replay_and_determinism` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| T | `external_decision_completeness` | AVAILABLE | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |

For all 20 rows: `semantic_precondition=null`, `action_decision_sequence=null`, `expected_semantic_outcome=null`, production qualification remains `NOT_RUN`.

## C01-C22 inventory

| ID | Requirement definition | Retained matrix source metadata | Exact semantic definition | Evidence |
|---|---|---|---|---|
| C01 | `40_starting_life` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C02 | `commander_starts_in_command_zone` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C03 | `cast_commander_from_command_zone` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C04 | `first_command_zone_cast_no_tax` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C05 | `second_same_commander_cast_plus_2` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C06 | `third_same_commander_cast_plus_4` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C07 | `partner_tax_independent` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C08 | `graveyard_command_zone_choice` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C09 | `exile_command_zone_choice` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C10 | `hand_library_replacement_choice` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C11 | `decline_zone_move_keeps_destination` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C12 | `declined_commander_moves_normally_afterwards` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C13 | `commander_damage_by_identity` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C14 | `20_commander_damage_not_loss` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C15 | `21_same_commander_damage_loss` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C16 | `damage_from_two_commanders_not_combined` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C17 | `commander_identity_through_copy_control_merge` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C18 | `four_player_commander_initialization` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C19 | `four_player_apnap` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C20 | `player_loss_game_continues` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C21 | `leaving_player_owned_objects_leave` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |
| C22 | `control_effect_cleanup_on_exit` | AVAILABLE_IN_SCENARIO_MANIFEST | SOURCE_DEFINITION_UNAVAILABLE | DIRECTLY_VERIFIED |

For all 22 rows: `semantic_precondition=null`, `action_decision_sequence=null`, `expected_semantic_outcome=null`, production qualification remains `NOT_RUN`.

## Gates

| Gate | Result |
|---|---|
| `A_T_source_inventory_count = 20` | PASS |
| `C01_C22_source_inventory_count = 22` | PASS |
| `unproven_invented_definitions = 0` | PASS |
| `every_missing_definition_classified_SOURCE_DEFINITION_UNAVAILABLE = true` | PASS |
| Named regression inventory | See `REGRESSION_SOURCE_INVENTORY.json/md` |

## WS07 boundary

WS07 may use these artifacts to identify authoritative requirement labels, but it must not convert a label into setup/actions/expected outcomes. Until a source-backed definition is recovered or separately authorized, every `SOURCE_DEFINITION_UNAVAILABLE` item remains non-executable for semantic qualification.
