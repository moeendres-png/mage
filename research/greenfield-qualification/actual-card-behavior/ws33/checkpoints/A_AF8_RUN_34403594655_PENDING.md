# WS33-A AF8 run 34403594655 — PENDING (reconciled, registered 2026-09-09)

Status: **PENDING**. `COVERAGE_PROMOTION=FALSE`. `COVERAGE_MUTATED=FALSE`.
Predecessor run `34377848619`: terminal FAIL, adjudicated (24 failures, all Profane +
strict-parser coverage consequence; 7/8 paths clean). Root causes classified in
`A_AF8_RUN_34377848619_FAIL.md`. This replacement is justified (not blind): it carries
the shared-dependency reconciliation that the coordinator finding prescribed — the
already-qualified AF8 line's authoritative bounded/X-mana option-domain mechanism
(`apply-ws33-bounded-number.py`, byte-identical to qualified AF8 HEAD `1922a5172f`),
which the failing A stack did not consume.

## Frozen registration

- SOURCE_HEAD: `b2289eb6e8ebe38b7a5e2f2996d64e125e0d0708` (run `headSha` verified equal)
- SOURCE_TREE: `6634ff3f2cf16fddf25f986b373f1ecbc1a99d5e`
- RUN: `34403594655`; JOB: `102641128995` (`af8`); dispatch: `workflow_dispatch` on
  `work/ws33-a-trigger-closure-20260907`
- Expected artifact: `ws33-abc-a-rest-svar-af8-34403594655` (retention 90d)
- Delta vs predecessor source `9d72a19288`: (1) new shared overlay
  `runtime-overlays/apply-ws33-bounded-number.py` byte-identical to the qualified AF8
  line; (2) workflow wires it (trigger path, post-input-confirm invocation, gate grep);
  (3) A hardener X policy accepts the overlay-externalized authoritative numeric kinds
  (`GUI_GET_INTEGER`/`NUMBER`/`NUMBER_ENUM`) while still selecting only the smallest
  positive among Forge-emitted options on the source-proven `Announce$ X` 1/1 shape;
  (4) A adjudicator X shape/presence rules accept the same three kinds; (5) adjudicator
  regression reworked (`CONFIRM_ACTION` wrong-kind) + new `NUMBER`/`NUMBER_ENUM`
  acceptance test.
- Immutable deps unchanged (FORGE_PIN `8c7e9afb`, route run/artifact/digest/source,
  WS01 `bf089ea8` / WS12 / WS32 / WS31-hist pins).

## What this run tests (coordinator question)

Whether the already-qualified AF8 bounded/X-mana mechanism source-authoritatively
enumerates the Profane Command legal X domain on the A stack: unbounded mana-X
(`max == Integer.MAX_VALUE`) is routed into `externalLegalXManaChoices`
(`ComputerUtilMana.canPayManaCost` over actual pool + battlefield production,
fail-closed otherwise) and externalized as exact `NUMBER_ENUM` options; the pilot
chooses smallest-positive among those options only. No new WS01 numeric/X contract,
no card-name branch, no hardcoded X ceiling, no pilot-derived legality, no GUI
fallback, no manual injection.

## Expected terminal shape (predicted, NOT a verdict)

- All steps green; adjudication PASS 8/8 with Profane carrying a `NUMBER_ENUM`
  `POSITIVE_X_ANNOUNCEMENT` selection row; Record/Replay byte-identical tapes/events/
  stages; per-path Decision+Hidden+Replay+target+selection evidence for all eight.

## Exact next action

Poll run `34403594655` to terminal status; download + verify + adjudicate its artifact
with the frozen adjudicator; on PASS, seal per-path evidence and hand off the eight
qualified candidates with unchanged `COVERAGE_PROMOTION=FALSE` (promotion is serial
and coordinator-gated). On FAIL, persist root-cause classification before any repair.

`TURN_STATUS=INTERRUPTED`. `TASK_COMPLETE=NO`.
