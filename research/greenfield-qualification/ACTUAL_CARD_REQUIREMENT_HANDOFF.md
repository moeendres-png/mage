# WORKSTREAM 02 — Actual-Card Oracle Requirement Corpus — Final Handoff

## Status

`WORKSTREAM_COMPLETE = TRUE`

WS02 is closed for the **identity/requirement corpus** scope. This handoff does **not** assert behavioral card coverage; LOADABLE / EXECUTABLE / DECISION_COMPLETE / HIDDEN_INFO_SAFE / REPLAY_SAFE remain downstream WS10 concerns.

## Canonical workstream coordinates

```text
WORKSTREAM_COMPLETE = TRUE
BRANCH = work/ws02-oracle-corpus-20260828
BASE_SHA = c0e42fb42c4a603aff4a76b1284f8271c12bfd42
BASE_TREE = fb06c61dd87b4b742722925cd7374d8f037e1f47
QUALIFICATION_HEAD = 56e82b8aeeb5059db46b3a5eea3abd05f5e1d3c6
QUALIFICATION_TREE = c22b60ec64d5f7a9f3e701524f73fac483e27762
HEAD = this handoff commit on BRANCH; resolve branch ref for the immutable final commit SHA
TREE = tree of this handoff commit; resolve branch ref / commit metadata for the immutable final tree SHA
EVIDENCE_CLASS = DIRECTLY_VERIFIED + CODE_DERIVED + EXTERNALLY_RULE_VALIDATED; MODELED only where explicitly marked
BLOCKERS = NONE
NEXT_ACTION = WS10 must consume this corpus and qualify behavior against the authoritative 1678-identity union; do not revive the historical 1721 target.
```

The self-referential handoff commit cannot embed its own Git SHA/tree. The immutable qualification state immediately before this Markdown file is `56e82b8a...` / tree `c22b60ec...`; the final handoff commit is the branch HEAD containing this file.

## Outcome

The authoritative requirement corpus is a strict deduplicated union of **1,678 Oracle identities** across all known required source classes, plus **142 explicit UNKNOWN real-opponent slots** that carry no Oracle ID and are not promoted into the union.

The historical target `1721` is superseded. It had been recorded before a materialized all-source Oracle-ID union existed. The materialized union is `1678`; the numerical delta is `-43`, exactly matching the 43 Dargo/Tymna candidate identities documented as consumed by the current RogShai list. Those 43 are also in `operational_own`, so they cannot be counted again in an Oracle-ID set union. No force-fitting was performed.

## Oracle corpus pin

The original 2026-08-27 historical Scryfall bulk qualification remains historical evidence, but its exact binary / Actions run was no longer retrievable during WS02 closeout. It was **not silently substituted**.

The corpus was explicitly re-pinned to a byte-verifiable c0 Actions artifact:

```text
run_id = 33176329547
artifact_id = 9687739211
artifact_name = greenfield-scryfall-oracle-qualification
artifact_zip_sha256 = 9dd003cc916b58aee3f7a56881b63ec0e7d2291501fa38f3d66cd285e682af4e
index_sha256 = 0fb351eae3e16a5739194835a8633187298c7660ef3712e21e5d5ca13d66327f
payload_sha256 = fd14481dae5029077ed00f8932e07acd6dc21a76d7aff8e287c5a93652d891b4
bulk_updated_at = 2026-08-28T09:01:56.722+00:00
oracle_identity_count = 38626
source_head = c0e42fb42c4a603aff4a76b1284f8271c12bfd42
source_tree = fb06c61dd87b4b742722925cd7374d8f037e1f47
```

Historical qualification pin retained for provenance:

```text
bulk_updated_at = 2026-08-27T21:01:57.237+00:00
payload_sha256 = 1f798bf1cae3129f46219d71fc9e0b04e593430f8c6b0acde0711b9c1ca679df
oracle_identity_count = 38626
availability_at_closeout = BINARY_AND_ACTION_RUN_NOT_RETRIEVABLE
```

## Required source classes

| Source class | Materialized requirement | Oracle identity treatment | Result |
|---|---:|---|---|
| `operational_own` | 1,007 operational identities | validated/resolved against corpus pin | PASS |
| `rogshai` | 100 slots / 87 distinct identities | exact NFC resolution | PASS |
| `kaervek` | 100 slots / 77 distinct identities | exact NFC resolution | PASS |
| `dargo_tymna` | 743 candidate identities | theorycraft candidate pool, not a physical deck | PASS |
| `official_precons` | 11 decks × 100 slots / 763 distinct identities | Forge extraction + official Wizards reconciliation + strict Oracle join | PASS |
| `unknown_real_opponents` | 142 unresolved slots | explicit `UNKNOWN`, no Oracle ID | PASS as explicit unknown requirement |

### Raw-source provenance hashes

```text
operational_own = fffd8afd77f674100312200bebcf360b6a20b2464a8090e257e45884bac9d37d
rogshai = 2991799ba720be02bca25f37dd6727935117f2f3ac11b11fc2d38719ae391cbe
kaervek = a4685705db515633415955147ae544c4b9698bb5308de9671dabf49cd4da8264
dargo_tymna = 084941f23fbf15a2fb5d1564049c0a8d5dce962a6ab20eef626e6ed777ab96c1
official_precon_forge_extraction = c58b325430dad5e987859fd92380f77083086df10e914066a105faf3cd6fcd2c
```

Dargo/Tymna source semantics remain explicit: candidate pool only; `physically_allocated=false`, `physically_built=false`, `purchased=false`, `reservation_created=false`.

## Unknown real opponents

Exactly **142** source slots remain intentionally unresolved:

- High Perfect Morcant: 46 UNKNOWN slots
- Cosmic Spider-Man: 96 UNKNOWN slots

Gate semantics:

```text
resolution_status = UNKNOWN
oracle_ids_promoted = 0
synthetic_promotion = false
unknown_slots_excluded_from_computed_oracle_id_count = true
```

UNKNOWN is not treated as a known-card PASS; the source class is nevertheless fully accounted for because every unresolved real slot is explicitly represented without invented identity.

## Official precon reconciliation

Forge extraction evidence:

```text
run_id = 33089467077
artifact_id = 9653672924
all_100_slots = true
```

All 11 required decks reconcile to official Wizards decklist pages and have 100 extracted slots:

1. Doom Prevails
2. Blight Curse
3. Dance of the Elements
4. Wakanda Forever
5. Lorehold Spirit
6. Scions & Spellcraft
7. Counter Intelligence
8. Turtle Power!
9. Silverquill Influence
10. The Fantastic Four
11. Avengers Assemble

Official sources used:

- Marvel Super Heroes Commander Decklists
- Lorwyn Eclipsed Commander Decklists
- Secrets of Strixhaven Commander Decklists
- FINAL FANTASY Commander Decklists
- Edge of Eternities Commander Decklists
- Teenage Mutant Ninja Turtles Commander Decklist

`OFFICIAL_PRECONS_RECONCILIATION.json` records `status=PASS`, `deck_count=11`, `all_100_slots=true`, no missing Forge names from official captures, and no basic-land quantity mismatch. Two TMNT page-rendering differences are explicitly enumerated (`and` vs `&`) and are **not fuzzy Oracle matching**.

## Resolution policy

The resolver/materializer contract is fail-closed:

```text
normalization = UNICODE_NFC_AND_TRIM
case_sensitive = true
fuzzy_matching = false
alias_matching = false
exact_card_face_name_matching = true
exact type-line discriminator permitted for ambiguity resolution
physical token exclusion = true
unique Oracle ID required = true
synthetic_promotion = false
behavior_promotion = false
```

Known-source closeout result:

```text
missing = 0
ambiguous = 0
oracle_ids_not_in_pinned_index = 0
ambiguous_promotions = 0
```

## Canonical union

`ACTUAL_CARD_REQUIREMENT_UNION.json` is PASS:

```text
status = PASS
complete = true
target_count = 1678
computed_oracle_id_count = 1678
member_count = 1678
unknown_real_opponent_slots = 142
unknown_slots_promoted_to_oracle_ids = 0
problems = []
missing_sources = []
```

Canonical membership is stored in seven SHA-pinned chunks using `uuid16-mask8-base64-v1`. Source-class bit assignments are:

```text
operational_own = 1
rogshai = 2
kaervek = 4
dargo_tymna = 8
official_precons = 16
```

Chunk counts: `250 + 250 + 250 + 250 + 250 + 250 + 178 = 1678`.

## Tests and reproducibility

No already-valid tests were rerun after the final packaging path was established.

Executed in this WS session before commit:

```text
resolver/materializer/packaging unit tests = 14 / 14 PASS
full-corpus materialization = PASS
computed_oracle_id_count = 1678
expected_oracle_id_count = 1678
unknown_slots = 142
known_source_missing = 0
known_source_ambiguous = 0
fuzzy_matching = false
synthetic_promotion = false
```

The final committed manifest/union/reconciliation values were subsequently read directly from GitHub and match the qualified outcome.

## Hard gates

```text
resolver_tests = PASS
materializer_tests = PASS
fuzzy_matching = false
synthetic_promotion = false
ambiguous_promotions = 0
oracle_ids_not_in_pinned_index = 0
all_required_source_classes_accounted_for = true
source_provenance_complete = true
explicit_unknown_slots_accounted_for = true
official_precon_reconciliation = PASS
ACTUAL_CARD_REQUIREMENT_UNION.status = PASS
computed_oracle_id_count = 1678
authoritative_target_count = 1678
target_count_equal = true
```

Therefore the WS02 identity/requirement gate is **PASS**.

## Files changed from audited base

The qualification branch is three commits ahead of `c0e42fb...` before this handoff commit. The content diff is restricted to WS02-owned actual-card requirement files:

```text
research/greenfield-qualification/ACTUAL_CARD_REQUIREMENT_MANIFEST.json
research/greenfield-qualification/ACTUAL_CARD_REQUIREMENT_ORACLE_PIN.json
research/greenfield-qualification/ACTUAL_CARD_REQUIREMENT_UNION.json
research/greenfield-qualification/actual-card-manifest/DARGO_TYMNA_CANDIDATES.json
research/greenfield-qualification/actual-card-manifest/KAERVEK_EXACT_100.json
research/greenfield-qualification/actual-card-manifest/OFFICIAL_PRECONS.json
research/greenfield-qualification/actual-card-manifest/OFFICIAL_PRECONS_RECONCILIATION.json
research/greenfield-qualification/actual-card-manifest/OWN_OPERATIONAL_1007.json
research/greenfield-qualification/actual-card-manifest/ROGSHAI_EXACT.json
research/greenfield-qualification/actual-card-manifest/UNION_MEMBERS_01.b64
research/greenfield-qualification/actual-card-manifest/UNION_MEMBERS_02.b64
research/greenfield-qualification/actual-card-manifest/UNION_MEMBERS_03.b64
research/greenfield-qualification/actual-card-manifest/UNION_MEMBERS_04.b64
research/greenfield-qualification/actual-card-manifest/UNION_MEMBERS_05.b64
research/greenfield-qualification/actual-card-manifest/UNION_MEMBERS_06.b64
research/greenfield-qualification/actual-card-manifest/UNION_MEMBERS_07.b64
research/greenfield-qualification/actual-card-manifest/UNKNOWN_REAL_OPPONENTS.json
research/greenfield-qualification/materialize_card_manifest.py
research/greenfield-qualification/test_materialize_card_manifest.py
research/greenfield-qualification/ACTUAL_CARD_REQUIREMENT_HANDOFF.md
```

No `ACTUAL_CARD_COVERAGE.*`, decision/hidden/RNG/Commander gate, canonical status, or architecture-final file is changed by WS02.

## Required handoff fields

```text
WORKSTREAM_COMPLETE = TRUE
BRANCH = work/ws02-oracle-corpus-20260828
BASE_SHA = c0e42fb42c4a603aff4a76b1284f8271c12bfd42
HEAD = branch HEAD containing this handoff file
TREE = tree of branch HEAD containing this handoff file
FILES_CHANGED = WS02-owned files listed above
TESTS = 14/14 PASS; full-corpus materialization PASS; committed manifest/union/reconciliation re-read from GitHub
RUN_IDS = 33176329547; 33089467077
ARTIFACT_IDS = 9687739211; 9653672924
EVIDENCE_CLASS = DIRECTLY_VERIFIED; CODE_DERIVED; EXTERNALLY_RULE_VALIDATED; MODELED only for explicitly labeled scheduling/interpretive metadata
GATES = PASS — 1678/1678 known Oracle union; 142 explicit UNKNOWN; zero missing/ambiguous/promoted IDs; precons PASS
BLOCKERS = NONE
DEPENDENCIES = downstream WS10 consumes this exact corpus; no unresolved WS02 upstream blocker
INTEGRATION_NOTES = authoritative target is 1678, not historical 1721; use ACTUAL_CARD_REQUIREMENT_ORACLE_PIN.json and chunked union as source truth; UNKNOWN opponent slots remain outside the Oracle union
NEXT_ACTION = integrate this WS02 handoff into WS10 Actual-Card Behavior Coverage and qualify behavior per the exact 1678 identities without changing identity semantics
```

## Integration contract for WS10

WS10 must consume, unchanged:

- authoritative target count: **1678**;
- corpus Oracle pin: `ACTUAL_CARD_REQUIREMENT_ORACLE_PIN.json`;
- source-class membership encoded by the seven union chunks;
- explicit 142 UNKNOWN slots with no Oracle-ID promotion;
- official-precon reconciliation as identity provenance only.

WS10 must not infer behavioral FULL from source presence, parsing, import, or this identity PASS. Behavioral fields remain independently fail-closed.
