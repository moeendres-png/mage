# WS33 serial integration (AF8 -> B) — Phase II AF8-first integration checkpoint

Date: 2026-09-09. Status: AF8_INTEGRATED=TRUE. `COVERAGE_PROMOTION=FALSE`.

## Integration method

Fast-forward-equivalent serial integration (no manual recreation of AF8 changes).
The integration branch history is linear: canonical base `6da237b7` -> ... -> AF8 HEAD
`1922a5172f0e004dd95c279744c641775a80b15a` (6 commits) -> integration commits.
`git merge-base --is-ancestor 1922a51 HEAD` = TRUE; AF8 HEAD is the direct parent of this line's first integration commit.

No source workstream branch was modified. No C/A/D/E/F content incorporated
(AF8 diff touches only the AF8 workflow, AF8 checkpoints, the bounded-number
overlay, the AF8 hardener, AF8 contract tests, and the Terra repair doc).

## AF8 repair substance (inherited verbatim)

- `runtime-overlays/apply-ws33-bounded-number.py` (new): externalizes bounded announce
  numbers; enumerates feasible external mana X. Wired into workflow trigger paths,
  harness invocation, and gate grep (`WS33_BOUNDED_NUMBER_EXTERNALIZED=PASS ... rules_mutation=0`).
- Workflow `ws33-abc-a-rest-svar-af8-runtime.yml`: fail-closed AF8 case-evidence
  reporting (`if: always()`), compact failure-evidence sealing bundle
  (`immutable-af8-evidence/` + `AF8_EVIDENCE_SHA256SUMS`, `if: always()`), artifact
  upload narrowed to the sealed bundle, fragile observation-samples `cmp` removed.
- `WS33_AF8_EVIDENCE_CONTRACT_REPAIR_TERRA.md` + observation-replay contract test +
  observation-transport-multiplicity acceptance + failure-evidence sealing commits.

## AF8 run/evidence identity (re-verified, not rerun)

- Run `34222323657` (`WS33 ABC A-rest SVar AF8 runtime`): completed SUCCESS at exactly
  AF8_SOURCE_HEAD on `work/ws33-af8-evidence-contract-repair-20260908` (live gh API).
- Artifact `10054400356`, digest `sha256:026df6dd6f770fe8f93c5efc96c17b2d473876a5b01f44d9ccbc24df96ae727c`.
- Downloaded artifact adjudication: `A_REST_SVAR_AF8_GATE.json` shows expected_paths=8,
  failure_count=0, failures=[], coverage_mutated=false, coverage_promotion=false;
  in-artifact `workflow-source-head.txt`/`workflow-source-tree.txt` exactly equal the
  AF8 source locks. AF8_EVIDENCE_STATUS=DIRECTLY_VERIFIED (run conclusion + artifact
  digest + gate + source binding).
- No expensive AF8 workflow rerun: integration impact analysis finds no source,
  semantic, or evidence invalidation (see below).

## Integration impact analysis (why no qualification rerun)

- Coverage-registry diff of the AF8 range restricted to ledger/queue/gate/operational
  state/manifest: EMPTY. AF8 integration changes zero coverage/identity state.
- AF8 file set is disjoint from B1/B2 campaign sources, queue definitions, the model
  manifest/consumer, the Forge pin, and the ABI validator. B1/B2 immutable evidence
  (runs `34266311850`/`34286249888`, PASS gates, artifact digests) is unaffected.
- Branch-level ledger still reads TOTAL=4188 PASS=285 UNKNOWN=3903 (B_UNKNOWN=675);
  operational successor truth (488/3700 via artifact `9979204198`) unchanged.
- PASS_EVIDENCE_INVALIDATED=FALSE. No B1/B2/AF8 rerun required or performed.

## Classification

Ancestry/integration facts: DIRECTLY_VERIFIED. AF8 run/artifact/gate: DIRECTLY_VERIFIED.
Impact analysis: CODE_DERIVED (file-set diff) + DIRECTLY_VERIFIED (live counts recomputed).

Next: Phase III B proposal precheck (recomputed disjointness incl. 488 operational PASS set),
then Phase IV PENDING before any registry mutation.

`COVERAGE_PROMOTION=FALSE`. `WS33_COMPLETE=FALSE`. `TASK_COMPLETE=NO`.
