# WS33 ABC — CLOSURE BOUNDARY

Date: 2026-09-05

Evidence classification: `DIRECTLY_VERIFIED` for current repository metadata; `CODE_DERIVED` for the frontier arithmetic and work-queue interpretation.

## Starting boundary

Post-G3 frontier:

- TOTAL 4188
- PASS 366
- UNKNOWN 3822
- FAIL 0
- UNSUPPORTED 0
- A179 / B675 / C700 / D920 / E1029 / F319 / G0 / H0

ABC scope is exactly `179 + 675 + 700 = 1554` currently UNKNOWN effective paths.

Current integrated work queue is schema `commander-simulator-next.ws33-integrated-work-queue.v1`, originally 3903 UNKNOWN paths / 236 work items. It groups effective path IDs by stable scenario group, runtime subsystem, logical bucket, owner family, and required evidence profile. G entries in that queue are now superseded only by the explicit G3-complete checkpoint; A–F entries remain unpromoted.

## Historical evidence compatibility boundary

The canonical Post-Gen2 audit consumption remains authoritative for reuse restrictions:

- WS27: `SYNTHETIC_ONLY`
- WS28: `SYNTHETIC_ONLY`
- WS29: `SEMANTICALLY_INCOMPATIBLE`
- WS30: `WITNESS_RERUN_REQUIRED`
- WS31: `WITNESS_RERUN_REQUIRED`
- WS32: prerequisite/failure-semantics evidence only; no behavior coverage
- historical qualification evidence is never promoted as Gen2 PASS without a fresh admissible witness
- no speculative Forge-core patch without a production-reachable actual-card failure
- no standalone `AbilitySub`, direct `effect.resolve(...)`, synthetic rules substitute, silent fallback, or manual generated-registry edit.

Therefore ABC cannot be closed by simply importing WS27/WS28 historical PASS labels. Fresh production-reachable actual-card witnesses are required for the ABC work items unless a later exact compatibility adjudication establishes stronger evidence.

## Required ABC execution strategy

ABC must be closed by scenario-group/runtime-subsystem campaigns, not by card-name/path-ID hacks. Each campaign must:

1. consume the current effective IDs and exact Forge/model lineage;
2. exercise actual source/card production reachability through Forge authority;
3. satisfy the work item's evidence profile (`STATE_ONLY`, `DECISION`, `RNG`, `HIDDEN`, `REPLAY` combinations);
4. preserve external-pilot-only discretionary choice;
5. retain principal-scoped observations where hidden identity is exposed;
6. use explicit RNG and tape-driven replay where required;
7. fail closed on unsupported production-reachable paths;
8. produce immutable per-path evidence before any coverage promotion.

No global A/B/C promotion is permitted from this boundary checkpoint.

## Operational note

ABC is materially larger than G3: 1554 paths across many scenario groups/runtime subsystems. The next implementation unit must therefore materialize a generic actual-card scenario-group runner/certifier from the existing WS33 registries and campaign infrastructure, then execute groups in resumable shards with one immutable checkpoint per terminal run. Reusing the integrated work queue is preferred to creating card-specific campaigns.

`ABC_STATUS = UNKNOWN`
`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
