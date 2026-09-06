# Commander Simulator Next — WS33 Long-Run Execution Contract

This file applies to branch `work/ws33-g3-final-closure-20260902` and the WS33 qualification work under `research/greenfield-qualification/actual-card-behavior/ws33/**`.

## Startup order

At the beginning of every continuation turn:

1. Read this `AGENTS.md`.
2. Read root `PROJECT_STATE.md`.
3. Read the WS33 continuation/handoff and the checkpoint named by `PROJECT_STATE.md`.
4. Re-verify the live relevant branch HEAD/TREE.
5. Re-read the active or most recent relevant GitHub Actions run/job/artifact state.
6. Resume from the first open item. Do not restart already validated phases without a concrete invalidation reason.

## Persistent execution discipline

Treat every model turn and every GitHub Actions run as interruptible.

After every material work package:

- persist code/evidence/checkpoints to GitHub;
- run or adjudicate the relevant deterministic validation;
- update `PROJECT_STATE.md` with the exact completed package, evidence classification, immutable identifiers, remaining blockers, and exact next action;
- never rely on chat-only state for a material fact needed to resume.

For a newly registered qualification run, immediately persist a PENDING checkpoint containing at least source HEAD, source TREE, RUN, JOB, expected artifact, immutable dependencies, and `COVERAGE_PROMOTION=FALSE`. The run source is frozen after registration.

At terminal status, persist PASS or FAIL before any repair or coverage promotion. On failure, persist the root-cause classification before changing the failed source. Historical or predecessor artifacts are immutable inputs, not mutable working state.

## WS33 evidence and rules boundary

- Rules Core owns legal actions, costs, mana, stack, priority, targets, combat, triggers, replacement/continuous effects, SBA, zones, and Commander rules.
- Pilots may choose only among authoritative actor/principal-scoped Decision Options.
- No prompt/UI rules heuristics, second hidden rules engine, first/default/random/pass/cancel/AI fallback, card-name production hacks, manual outcome injection, direct `sa.resolve()` substitute, or standalone `AbilitySub` substitute for a production-reachable consumer.
- Unsupported production-reachable paths fail closed.
- `UNKNOWN` is not PASS. `PARTIAL` is not FULL.
- Evidence classifications are `DIRECTLY_VERIFIED`, `CODE_DERIVED`, `TECHNICALLY_CONFORMANT`, `EXTERNALLY_RULE_VALIDATED`, `MODELED`, `SYNTHETIC`, `UNKNOWN`.
- A green workflow alone is not a qualification PASS; artifacts and gates must be independently adjudicated.
- Coverage promotion is serial and deterministic only after immutable witness/certification evidence is independently verified.

## Canonical WS33 completion gate

`TASK_COMPLETE = YES` and `WS33_COMPLETE = TRUE` are allowed only after the complete original WS33 scope has been rechecked and all of the following hold simultaneously:

- effective paths = 4188;
- PASS = 4188;
- UNKNOWN = 0;
- FAIL = 0;
- UNSUPPORTED = 0;
- A-H UNKNOWN = 0;
- all required Rules/Decision/RNG/Replay/Hidden/Failure/evidence/hash gates are valid;
- final serial cross-qualification and project reconciliation are complete;
- no material TODO remains.

Architecture Freeze must be separately adjudicated from those verified facts. Do not infer it from workflow greenness.

## Turn boundary

If a model turn ends before the completion gate is satisfied, repository state must say:

`TURN_STATUS = INTERRUPTED`
`TASK_COMPLETE = NO`

A later `FORTSETZEN` / `WORKSTREAM FORTSETZEN` resumes from `PROJECT_STATE.md` and the referenced checkpoint, not from Phase 1.
