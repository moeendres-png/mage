# Commander Simulator Next — Active Routed Task Index

This index is dispatch metadata, not qualification evidence. Always verify live branch identity before execution.

## WS33 current queue

### P0 — AF8 evidence-contract repair

```text
ROUTE = NORMAL_SOL_ANALYSIS -> TERRA_IMPLEMENTATION -> NORMAL_SOL_REVIEW
EXECUTION_BRANCH = work/ws33-af8-evidence-contract-repair-20260908
BASE = 6da237b704ba5e66c58c2334f47e36ef68ca980d
INITIAL_TASK_PACKET_COMMIT = d1ca56293ca2c919511a787a079cc7c885939116
PACKET_PATH = research/greenfield-qualification/agent-workflow/tasks/WS33_AF8_EVIDENCE_CONTRACT_REPAIR_TERRA.md
CURRENT_FAILURE_CLASS = QUALIFICATION_EVIDENCE_CONTRACT_MISMATCH
SOL_CODEX_REQUIRED = FALSE
```

The packet is intentionally stored on its isolated execution branch because it binds directly to the exact AF8 repair base. Do not copy it onto a newer execution base without re-verifying the frozen run/job/artifact evidence and current canonical source.

### A–F isolated high-throughput dispatch

Central prompt bundle:

`WS33_A_F_TERRA_DISPATCH_20260908.md`

Inspected initial branch identity:

```text
HEAD = 895240f4058076764227a418ad28e84f61d3a7ed
TREE = cec73ae51b0168280ea648892f3e9edd46dcd883
```

Branches:

```text
work/ws33-a-trigger-closure-20260907
work/ws33-b-high-throughput-20260907
work/ws33-c-high-throughput-20260907
work/ws33-d-high-throughput-20260907
work/ws33-e-high-throughput-20260907
work/ws33-f-high-throughput-20260907
```

Before execution, preserve any commits that have appeared since this index was written. Never reset an advanced workstream branch back to the inspected identity.

## Current non-queue families

At the 2026-09-08 routing snapshot:

```text
G_UNKNOWN = 0
H_UNKNOWN = 0
```

Do not schedule routine G/H work unless a later code/pin/contract change invalidates their evidence.

## Integration rule

Isolated workstreams produce branch-local evidence only. Canonical coverage promotion is a separate serial cross-certification step.