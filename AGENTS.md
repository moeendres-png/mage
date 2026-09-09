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

## OpenCode execution-model contract

All Commander Simulator Next repository execution performed through OpenCode is restricted to **OpenCode Go + Muse Spark 1.3 Contributor**.

Authoritative OpenCode provider ID:

`opencode-go`

Authoritative Go model ID:

`muse-spark-1.3-contributor`

Authoritative full OpenCode model selector:

`opencode-go/muse-spark-1.3-contributor`

The repository `opencode.json` is the executable project configuration for this policy.

### Go-only provider policy

Project execution must use **OpenCode Go**, not OpenCode Zen.

The Zen model `opencode/muse-spark-1.3-contributor-free` is a different provider/SKU and is not authorized for project execution while this Go-only policy is active.

Do not silently route through Zen, Zen Free, another OpenCode provider, or any third-party provider if the Go model is unavailable.

### Allowed reasoning range

Only these reasoning variants are authorized for project work:

- `medium`
- `high`
- `xhigh`

Default for substantive implementation, debugging, qualification, integration, and evidence work is `high`.

Use `medium` for bounded mechanical/read-heavy work where higher reasoning has no material expected benefit.

Use `xhigh` for difficult root-cause analysis, complex multi-file repair, subtle semantic integration, or other tasks where the additional reasoning budget is justified.

`none`, `minimal`, `low`, and `max` are outside the project-authorized range and must not be used.

### No model or provider fallback

Do not switch to another model family, another Muse version, another Muse SKU, a generic small model, OpenCode Zen, or another provider when `opencode-go/muse-spark-1.3-contributor` is unavailable, rate-limited, missing from the catalog, or errors.

Fail closed instead:

1. preserve current work and evidence;
2. record the exact OpenCode version, provider ID, requested model ID, requested variant, and error;
3. classify the condition as `EXECUTION_MODEL_UNAVAILABLE`;
4. stop model-dependent execution and hand back the blocker.

Do not silently use Muse Spark 1.2, Muse Spark 1.3 Contributor Free on Zen, another Muse Spark route, GPT, Claude, Gemini, DeepSeek, or any other substitute.

A change of provider/SKU requires explicit coordinator/user authorization because it may change cost, service contract, privacy/training terms, routing behavior, or evidence environment.

### Agent and subagent model inheritance

Primary agents, planning agents, exploration agents, summary/title/compaction helpers, and any custom/subagent used for project work must remain on the same authoritative Go model:

`opencode-go/muse-spark-1.3-contributor`

Before using a newly configured custom agent or subagent, verify its effective provider, model, and variant.

Do not delegate to a subagent if OpenCode cannot prove that its effective provider is `opencode-go`, its effective model is `muse-spark-1.3-contributor`, and its reasoning variant is `medium`, `high`, or `xhigh`.

### Effective-config verification

At the beginning of a new OpenCode workstream, or after any OpenCode/provider/config change:

1. read `opencode.json` and this `AGENTS.md`;
2. verify OpenCode's live `/models` catalog under the connected **OpenCode Go** provider contains `opencode-go/muse-spark-1.3-contributor`;
3. verify the effective agent provider is `opencode-go`;
4. verify the effective agent model is `muse-spark-1.3-contributor`;
5. verify the effective variant is `medium`, `high`, or `xhigh`;
6. run a minimal non-mutating model-identity smoke check when the OpenCode version/provider configuration has changed materially;
7. if any check fails, fail closed before material repository mutation.

Do not rely only on a requested CLI `--model` / `-m` string as proof of the effective model. Verify the effective session/provider/model identity because OpenCode versions may have model-selection or fallback defects.

CLI `--model` / `-m`, session model changes, custom commands, custom agents, or user/global configuration must not be used to bypass this project policy.

If a higher-precedence user/global OpenCode configuration prevents this project policy from taking effect, report the conflict explicitly rather than silently continuing.

## Turn boundary

If a model turn ends before the completion gate is satisfied, repository state must say:

`TURN_STATUS = INTERRUPTED`
`TASK_COMPLETE = NO`

A later `FORTSETZEN` / `WORKSTREAM FORTSETZEN` resumes from `PROJECT_STATE.md` and the referenced checkpoint, not from Phase 1.
