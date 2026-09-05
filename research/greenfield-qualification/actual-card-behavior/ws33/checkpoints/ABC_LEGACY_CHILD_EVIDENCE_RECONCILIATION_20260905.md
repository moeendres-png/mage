# WS33 ABC — LEGACY CHILD EVIDENCE RECONCILIATION

Date: 2026-09-05

Evidence classification: `DIRECTLY_VERIFIED` for live branch/run/job/log facts; `CODE_DERIVED` for current compatibility conclusions.

## WS33A legacy child

Branch `work/ws33a-targetrestrictions-closure-20260831` exists at HEAD `95e5dc2c8782de9f5d848f0c213846dc0fecd758`, tree `bd90c8670c5e8ff46a836a92bfb97e9c36c7722c`.

Its only child tooling is a lookup probe (`apply_ws33a_lookup_probe.py`, `ws33a_prepare_lookup_probe.py`) plus workflow `.github/workflows/ws33a-targetrestrictions-lookup-probe.yml`.

Terminal run `33377220643`, job `99441304061`, concluded success only because the workflow explicitly accepted the diagnostic result `WS33A_LOOKUP_PROBE=BLOCKED` / `WS33A_CHILD_COMPLETE=FALSE`. The actual runtime probe failed in `CardFactoryUtil.getCard` with `NullPointerException` because the diagnostic invoked the target-restrictions lookup without a production card database.

Adjudication: useful root-cause/tooling evidence only; **zero current ABC PASS paths**.

## WS33B legacy child

Branch `work/ws33b-cost-amount-closure-20260831` exists at HEAD `edd5cf43ab9a6288a2d91db603cb4ad24d7f36bf`, tree `477cf1abe7b09f0ff84383981febbc66553a1b43`.

Terminal run `33375610646`, job `99436291615`, concluded success as a shared-blocker evidence workflow. It directly reported:

- `WS33B_ASSIGNED_PATHS=598`
- `WS33B_COST_PATHS=396`
- `WS33B_AMOUNT_PATHS=202`
- `WS33B_SHARED_MODEL_MISCLASSIFIED_PATHS=10`
- `CROSS_SHARD_SHARED_BLOCKER=TRUE`
- `WS33B_CHILD_COMPLETE=FALSE`

Its gate deliberately required PASS=0 / UNKNOWN=598. It therefore supplies model/root-cause evidence, not qualification coverage.

The shared model defect was subsequently repaired by the Parallel Base V2 work and is already reflected in the current 4188 effective model. The child run itself remains non-promotable.

Adjudication: useful historical shared-model evidence; **zero current ABC PASS paths**.

## WS33C legacy child

Branch `work/ws33c-abilitysub-api-closure-20260831` exists at HEAD `c69686431c7296cb3e1a2f9e0de8b82886c92c46`, exactly the old parallel base head; it contains no child-specific delta relative to that base.

Adjudication: no completed WS33C child evidence to import; **zero current ABC PASS paths**.

## Consequence for current ABC closure

The live child branches confirm that A/B/C were not independently completed after the shared model repair. They cannot close the current A179/B675/C700 frontier by compatibility import.

Current ABC still requires fresh production-reachable actual-card execution under the current effective model. Legacy A/B tooling may be mined for instrumentation patterns and known failure modes, but not counted as PASS.

`ABC_IMPORTED_PASS = 0`
`ABC_UNKNOWN = 1554`
`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
