# G3 NON-AF EVENT RUNTIME — RUN 33816948410 FAILURE

Evidence classification: `DIRECTLY_VERIFIED` for run/artifact/gate facts; underlying resolution root cause remains `UNKNOWN` and is deliberately not guessed.

## Immutable run identity

```ini
EVIDENCE=DIRECTLY_VERIFIED
RUN=33816948410
JOB=100851076967
SOURCE_HEAD=3bf09bc325ee5094d2a4874bbc133520f5f759dc
SOURCE_TREE=8e0a65344e4257fa51e2b15dfdac35e4883bd9ae
ARTIFACT=9916940071
ARTIFACT_DIGEST=sha256:4e1ed01602e46b796bdcd257964e9fc56d32aa370112c94cc57c64d8ef8b0871
RECORD_CAMPAIGN=PASS
RECORD_ADJUDICATION=FAIL
REPLAY=NOT_RUN
COVERAGE_PROMOTION=FALSE
G3_NON_AF_STATUS=UNKNOWN
```

The downloaded ZIP was independently SHA-256 hashed before inspection and matched the GitHub artifact digest exactly.

## First material Step-15 failure

Step 14 (`Execute 33-parent record campaign`) completed successfully. Step 15 (`Adjudicate record behavior and minimum Decision/RNG obligations`) again failed first in the parent-runtime predicate, before path-summary, Decision, or RNG adjudication.

The first parent row in artifact order is now:

```text
forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8	1	1	f3988b96-9e00-445c-b3e1-6b2df9b13dac	Ingenious Smith	ChangesZone	TRIGGER		TrigDig	Dig	FAIL	1	1	0	...
```

Decoded failure:

```text
java.lang.IllegalStateException
target SVar did not reach non-fizzled root resolution parent=forge-behavior-v2:172ab06795f99590ca9d96f85995f6cf9e083ee8#1
```

This is materially different from run `33798608932`: the same ChangesZone parent now records exactly one legal trigger admission and exactly one target binding (`1/1`) after the production-runParams fixture repair. The previous enum-vs-string ChangesZone fixture defect is therefore removed at the first-parent gate.

## Current classification

```ini
FIRST_FAILURE_CATEGORY=effective-path reachability failure
TRIGGER_ADMISSION=PASS
TARGET_BINDING=PASS
TARGET_EXECUTION=FAIL
UNDERLYING_ROOT_CAUSE=UNKNOWN
```

Artifact-wide supporting facts, not yet individually repaired:

```text
33 parent rows
1 PASS
24 FAIL with admission/binding/execution = 1/1/0
8 other FAIL rows with earlier admission/event-specific failures
```

Only `Descendants' Fury` reached `1/1/1` in this artifact. Later Phase, AttackersDeclared, Study Hall, and other event-specific failures remain downstream symptoms and are not repair targets until the first parent failure is resolved.

## Why the root cause is intentionally still UNKNOWN

Pinned Forge source proves that TriggerHandler admits a source-proven ability and wraps it for the simultaneous stack, and MagicStack's observation-only hook is placed after fizzle adjudication immediately before `AbilityUtils.resolve(sa)`. However, artifact `9916940071` alone does not distinguish between:

1. the admitted target ability failing to become/resolve as the production stack ability, and
2. the production stack ability reaching the resolution hook but no longer matching the harness' script-equality identity test after normal production preparation.

No decision/RNG request for the first path provides an independent proof of target effect execution. Therefore treating either explanation as established would be speculation.

## Narrow next diagnostic scope

Before any semantic or matcher repair, add observation-only, fail-closed resolution telemetry that records every MagicStack resolution-observer callback while a parent key is active, including stable runtime identity fields needed to compare the admitted ability to the resolving ability (wrapper state, ability id/source-trigger id, host id, API, and immutable/current map fingerprints). Do not change the existing PASS predicate in the diagnostic run.

This diagnostic must not alter legality, target selection, choices, stack order, fizzle adjudication, resolution, Decision/RNG evidence, or coverage.

## Resume

1. Update `WS33_CONTINUATION_HANDOFF.md` with this terminal failure.
2. Persist an observation-only diagnostic instrumentation commit; do not repair the unknown cause yet.
3. Trigger exactly one event-runtime run from that diagnostic commit.
4. Persist its pending run identity immediately.
5. Adjudicate the new immutable artifact to distinguish stack-placement/non-resolution from resolution-identity measurement failure.
6. Only then repair the confirmed systemic cause.
