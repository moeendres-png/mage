# Commander Simulator Next — AI Engineering Routing

Status: project workflow policy, not qualification evidence.

This file defines how to route work among normal GPT-5.6 Sol chat, Codex Terra, Codex Luna, Codex Sol, and optional local models without weakening Commander Simulator Next's technical contracts.

## Principle

Choose the cheapest model that can safely execute the already-understood task. Do not use a stronger model as a substitute for precise scope, exact source identity, or reproducible evidence.

Model choice does not change Rules authority or evidence standards.

## Default routing

| Work type | Route |
|---|---|
| Architecture, root-cause analysis, official-rules adjudication, workstream decomposition | normal GPT-5.6 Sol chat |
| Bounded multi-file implementation, witness/campaign work, adapters, harnesses, ordinary bugs/refactors | Codex Terra |
| Mechanical follow-up after semantics are fixed | Codex Luna |
| P0/P3/P5-class hard repair, persistent replay/concurrency issue, or repeated Terra failure | Codex Sol |
| Non-canonical local boilerplate/log/CSV/JSON assistance | local model |

## Normal Sol chat responsibilities

Use Sol before repository implementation when the task has one or more of these properties:

- architecture or subsystem ownership is unclear;
- the root cause is not established;
- official Magic rules must adjudicate expected behavior;
- an existing PASS set may be invalidated;
- hidden information, RNG, replay, replacement effects, layers/copy/control, multiplayer combat, or failure semantics are materially involved;
- multiple implementation strategies have materially different blast radius;
- a precise Codex work packet would avoid expensive repository exploration.

A Sol planning result should produce a complete task packet rather than vague prose.

## Codex Terra — default implementation worker

Use Terra for the majority of repository work once the task is bounded.

Typical Terra work:

- implement an actual-card witness campaign;
- modify several related files in one owned subsystem;
- build or repair an adapter;
- integrate an already-defined contract;
- add focused regression coverage;
- perform normal refactoring;
- materialize deterministic path/cluster manifests;
- repair a qualification harness when the semantic role is already established.

Terra must still verify the exact base and obey all repository/workstream contracts.

## Codex Luna — mechanical follow-up only

Use Luna only after the semantic decision is fixed.

Good Luna work:

- documentation and handoff updates;
- lint/format cleanup;
- repetitive fixture normalization;
- already-specified edge-case tests;
- mechanical renames;
- log/evidence-table transformation;
- obvious local compiler/type fixes that do not alter semantics.

Luna must escalate instead of improvising if a task requires changing:

- Rules semantics;
- legal-action generation;
- costs or mana semantics;
- target legality;
- trigger/replacement/layer semantics;
- hidden-information boundaries;
- RNG/replay contracts;
- failure-category meaning;
- the effective-path model.

## Codex Sol — escalation only

Escalate to Codex Sol when evidence establishes at least one of:

1. two materially different, technically sound Terra attempts failed on the same root cause;
2. a model/core representation defect is likely (`P0`);
3. a generic engine Rules-Core defect is likely (`P3`);
4. an architecture boundary is implicated (`P5`);
5. persistent nondeterminism/replay failure cannot be localized;
6. concurrency/process-isolation is likely causal;
7. a central migration has unusually large blast radius and high cost of error.

Do not escalate merely because a task is large. Split large work into coherent testable packages first.

## Root-cause classes

Use these labels when useful:

- `P0` — model/core representation
- `P1` — witness/campaign gap
- `P2` — adapter/externalization gap
- `P3` — generic engine rules-core gap
- `P4` — cross-cutting rules complexity
- `P5` — architecture boundary

Also classify the immediate engineering defect explicitly, for example:

- `WITNESS_GAP`
- `ADAPTER_GAP`
- `ENGINE_GAP`
- `MODEL_GAP`
- `TEST_GAP`
- `REPLAY_GAP`
- `FAILURE_SEMANTICS_GAP`
- `QUALIFICATION_EVIDENCE_CONTRACT_MISMATCH`
- `INTEGRATION_GAP`
- `UNKNOWN`

Do not equate an `UNKNOWN` path with an engine bug.

## Standard lifecycle

For substantial work:

```text
1. Sol or current workstream establishes exact source/evidence state.
2. Create a bounded task packet.
3. Terra implements and runs focused validation.
4. Luna performs only safe mechanical cleanup if useful.
5. Sol adversarially reviews central/high-risk changes.
6. Persist evidence, exact identities, and handoff.
7. Integrate/cross-qualify separately where required.
```

## Terra failure rule

After a Terra failure, do not automatically escalate.

First distinguish:

- environmental/tool failure;
- stale source/base;
- incorrect task packet;
- insufficient evidence;
- implementation defect;
- wrong root-cause classification.

After two genuine repair attempts against the same confirmed hard root cause, use a Sol root-cause pass. Only then decide whether Codex Sol is justified.

## Local GPU helper

A local model on the RTX 2080 may reduce cloud usage for non-canonical routine work, but its output is proposal-only.

Allowed examples:

- summarize logs;
- generate candidate test matrices;
- transform CSV/JSON;
- draft documentation;
- regex/boilerplate;
- explain code;
- suggest edge cases.

Its output classification is:

```text
LOCAL_OUTPUT_CLASS = NON_CANONICAL_CANDIDATE
```

A local model cannot establish current GitHub truth, Magic rules correctness, behavior PASS, replay correctness, or qualification PASS.

## Prompt discipline

Never send Codex an instruction such as `improve the simulator`.

Every substantial repository task should state:

- task ID;
- model route;
- repository;
- exact base SHA/tree when available;
- target branch;
- goal;
- in/out scope;
- owned files/subsystems;
- dependencies;
- evidence already known;
- implementation plan;
- forbidden shortcuts;
- test plan;
- validation commands;
- pass/fail semantics;
- evidence outputs;
- handoff requirements;
- Definition of Done.

Use `TASK_PACKET_TEMPLATE.md` as the canonical drafting skeleton.