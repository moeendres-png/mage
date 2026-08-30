# WS30 — COMBAT / COMMANDER ACTUAL-CARD CLOSURE — HANDOFF

## Qualification status

The immutable evidence committed with this handoff was produced by a complete WS30 full-pass run and independently rechecked before commit. The commit containing this handoff must itself pass the restored WS30 qualification workflow before final closure.

- `WS30_FAMILY_GATE = PASS`
- `WORKSTREAM_COMPLETE = TRUE`
- Owner family: `COMBAT_COMMANDER`
- Assigned V2 paths: **27**
- Actual-card PASS witnesses: **27**
- Inherited PASS witnesses: **0**
- Missing / extra / duplicate paths: **0 / 0 / 0**
- Global Q5 rerun: **false**
- Global Q6 claim: **false**

## Immutable predecessor boundary

- WS26 HEAD: `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef`
- WS26 TREE: `837f445f78bb26462653c58baf1532e294151b10`
- WS26 run: `33283478862`
- WS26 job: `99182488884`
- WS26 artifact: `9723722686`
- WS26 artifact digest: `sha256:b9e1fc4fd792b0baa1da1c17e3bbc9e01b2557d4b73b8590e680679f53b59883`

## Pinned engine

- Card-Forge/forge: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- No Forge production source was modified; WS30 uses a qualification-only test overlay against this exact pin.

## Full-pass evidence source

- Qualification HEAD: `38d2db6eae131bef1e7079eb80e6c012b9badbdf`
- Qualification TREE: `f55320645dfa63920954ebc2b292ccfc90128db7`
- Run: `33316335525`
- Job: `99270369522`
- Artifact: `9733584180`
- Artifact digest: `sha256:e31b939402e4b59db711a2bdf29773f4cb7be8d0ea434224256f5b3459a92199`
- Test / materialize / gate / replay exit codes: `0 / 0 / 0 / 0`

`WS30_HASHES.sha256` was independently verified. The five semantic evidence products from primary execution and replay compare byte-for-byte identical.

## Required hard gates

- `combat_legality_from_rules_core = true`
- `manual_combat_legality_in_harness = 0`
- `combat_state_assertions_complete = true`
- `commander_specific_paths_rules_validated = true`

First strike, double strike, goad, blocking/evasion, removal from combat, Commander identity, and same-Commander combat damage are qualified by actual pinned-Forge execution.

## Rules / pilot boundary

Attacker declaration consumes `Combat.getAttackConstraints().getLegalAttackers()` and is checked by `CombatUtil.validateAttackers`. Block legality is queried through `CombatUtil.canBlock` and validated through `CombatUtil.validateBlocks`. Combat damage is resolved by Forge combat-phase machinery. The harness does not reimplement combat rules or use silent default/random/pass fallbacks.

## Aura bootstrap closure

The earlier Aura failure was a standalone-test bootstrap defect. `PaperCard` contained `Enchantment - Aura`; runtime construction lost `Aura` because Forge's dynamic subtype registry had not been initialized. WS30 now follows Forge's product initialization path via `FModel.loadDynamicGamedata()` before runtime card construction and asserts `CardType.Constant.LOADED`. No `setType`, card-name subtype patch, manual Aura injection, or SBA bypass was added.

## Multiplayer Ghostly Prison closure

In 4-player Commander the attack tax is defender-scoped. Forge can satisfy a must-attack requirement by selecting an untaxed legal opponent rather than globally omitting the attacker. The witness asserts the actual rules-core-selected defender and does not impose a 2-player heuristic.

## Semantic replay normalization

Java default `Object.toString()` heap identities for `AttackRestriction` and `AttackRequirement` are incidental JVM data. Materialization replaces only those addresses with a stable `[present]` marker, preserving the constraint class and every legal/result/state assertion. No semantic choice or game state is normalized away.

## Rules authority and evidence classes

Official Magic Comprehensive Rules effective **2026-08-07** are semantic authority, including relevant rules 508, 509, 510, 701.12, 701.15, 702.4, 702.7, 702.9, 702.83, 702.91, 702.121, 903.3, 903.9, and 903.10a. Forge parity is implementation evidence only.

- WS26 boundary / Forge pin / artifact hashes / replay identity: **DIRECTLY_VERIFIED**
- 27/27 actual-card execution: **TECHNICALLY_CONFORMANT**
- Official combat/Commander adjudication: **EXTERNALLY_RULE_VALIDATED**
- Global Q6: **NOT CLAIMED**

## Committed evidence

- `actual-card-behavior/ws30/WS30_WITNESSES.jsonl`
- `actual-card-behavior/ws30/WS30_PATH_COVERAGE.json`
- `actual-card-behavior/ws30/WS30_COMBAT_INVENTORY.json`
- `actual-card-behavior/ws30/WS30_COMMANDER_INVENTORY.json`
- `actual-card-behavior/ws30/WS30_RULES_ADJUDICATION.json`
- `actual-card-behavior/ws30/WS30_GATE.json`
- `actual-card-behavior/ws30/WS30_HASHES.sha256`
