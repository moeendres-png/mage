# ABC-D1 lifegain run 34348893940 — PENDING (registered)

Date: 2026-09-09 (post-restart resume). Branch: `work/ws33-d-high-throughput-20260907`.
TERMINAL_RESULT=PENDING. COVERAGE_PROMOTION=FALSE. WRITE_FREEZE in effect
for D1 machinery/paths until terminal adjudication.

## Frozen run source

- SOURCE_HEAD=`c1049124559a80bb7838638599f5e726805bc145`
  (contains: D1f FAIL adjudication + D1g semantic-match repair)
- RUN=`34348893940` (head_sha verified equal to SOURCE_HEAD at registration)
- EXPECTED_ARTIFACT=`ws33-abc-d1-lifegain-34348893940`

## D1g content (narrow D-local provider repair)

- ENTITY_LIST_SELECTION matches the entity-denoting option by semantic
  value `"ENTITY:" + optionIdFor(designated)` (bridge models entity
  selection as DISCRETE options); requires exactly one such option,
  CANCEL-only companions with cancel disallowed and min>=1.
- Resolution basis made consistent per branch (record: semantic vs
  semantic; replay: id|semantic pair vs pair); certifier asserts
  resolution==tape count with all matched (new `expected_select` /
  `selected` keys).
- Intent protocol, fixtures, selection, pins, TARGET_DIGEST
  (`7de91571...`) unchanged; workflow unmodified.

## Local validation performed (this failure class)

py syntax; javac with zero non-dependency errors; preparer+filter
dry-run against pinned scripts with digest reproduced; certifier
fail-closed negative control on the partial D1f artifact; new-key
logic positive evaluation. Full Forge runtime reproduction is not
available locally; the cloud run is the runtime validation, gated
fail-closed.

## Exact next action

Poll run 34348893940 to terminal; adjudicate artifact independently.
On full PASS (10 markers + index + empty diagnostics + gate): repartition
per the D1 contract and build D2 runtime. On fail: root-cause first.
