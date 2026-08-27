# Actual Card Requirement Manifest — Current Qualification State

Status: **INCOMPLETE / FAIL-CLOSED**.

The manifest derives the target from its versioned `oracle_union.target_count`
field, currently **1,721**. It does not hard-code that number in the
materializer.

The live Scryfall source is independently indexed and hash-recorded in
`SCRYFALL_ORACLE_INDEX_QUALIFICATION.json`. The project-specific union is not
complete because the research checkout contains only descriptor files for the
own 1,007-card operational pool and the exact 100-slot Kaervek deck. Those
descriptors deliberately do not embed Drive-domain rows or Oracle IDs.

Consequences:

- current union status: `NOT_RUN`, computed IDs `0`;
- no name-based or synthetic identity promotion;
- source classes still required: operational own, RogShai, Kaervek,
  Dargo/Tymna, official precons, and unknown real opponents;
- per-identity behavior, decision, hidden-information, and replay flags remain
  unassessed.

The Drive workbook was read-only input only. No Drive file, deck, inventory,
allocation, purchase, or playtest state was changed.
