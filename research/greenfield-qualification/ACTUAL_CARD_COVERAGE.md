# Actual Card Coverage — Current Qualification State

Status: **INSUFFICIENT EVIDENCE**.

The current Scryfall Oracle Cards gzip/JSONL ingest passed independently:

- bulk updated: `2026-08-27T21:01:57.237+00:00`;
- deduplicated upstream Oracle identities: **38,626**;
- payload SHA-256: `1f798bf1cae3129f46219d71fc9e0b04e593430f8c6b0acde0711b9c1ca679df`.

This is only the neutral upstream index. The project-specific requirement
union target is **1,721**, but the available own-inventory and Kaervek
research files are descriptors without materialized `oracle_id` rows. The
union therefore remains `NOT_RUN` at **0/1,721**. No card-name join, synthetic
promotion, or inferred Oracle identity is accepted.

The required per-identity fields remain separate:

```text
PRESENT, LOADABLE, EXECUTABLE, DECISION_COMPLETE,
HIDDEN_INFO_SAFE, REPLAY_SAFE, behavioral_evidence
```

They are not promoted from source presence, parsing, deck loading, or card
count. `ACTUAL_CARD_COVERAGE.json` and
`ACTUAL_CARD_REQUIREMENT_UNION.json` contain the machine-readable status.
