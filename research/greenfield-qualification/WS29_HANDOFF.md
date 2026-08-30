# WS29 — CONTINUOUS / COPY / CONTROL CLOSURE

## Terminal adjudication

```text
WS29_FAMILY_GATE = FAIL_CLOSED
WORKSTREAM_COMPLETE = FALSE
WORKSTREAM_CLOSED_FAIL_CLOSED = TRUE
qualification_execution_complete = TRUE
SHARED_CORE_FIX_REQUIRED = FALSE
UPSTREAM_MODEL_FIX_REQUIRED = TRUE
Q6_ACTUAL_CARD_BEHAVIOR = NOT_ADJUDICATED_BY_WS29
```

WS29 is closed **fail-closed**, not qualified as a family PASS. A successful WS29 GitHub Actions run means the qualification procedure completed and emitted internally consistent terminal evidence; it does **not** mean the 301 production-required behavior paths passed semantic qualification.

## Canonical boundary

- Repository: `moeendres-png/mage`
- Branch: `work/ws29-v2-continuous-copy-control-20260830`
- Owner family: `CONTINUOUS_COPY_CONTROL`
- WS26 base HEAD: `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef`
- WS26 base TREE: `837f445f78bb26462653c58baf1532e294151b10`
- WS26 immutable artifact: `9723722686`
- WS26 artifact digest: `sha256:b9e1fc4fd792b0baa1da1c17e3bbc9e01b2557d4b73b8590e680679f53b59883`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Assigned V2 paths: `301`

The final workflow artifact's `WS29_PROVENANCE.json` is authoritative for the exact tested WS29 HEAD/TREE. Integration must verify the final branch run, job, artifact ID and digest live rather than treating this filename as freshness proof.

## Qualification result

All 301 assigned paths are accounted for. No WS29 V2 path currently has an admissible semantic PASS witness satisfying the WS26 V2 witness ABI, so the terminal semantic inventory is:

```text
PASS        = 0
FAIL        = 0
UNSUPPORTED = 0
UNKNOWN     = 301
```

Path-required evidence that remains unproved:

```text
authoritative decision evidence = 218 paths
RNG evidence                    = 157 paths
hidden-information evidence     = 34 paths
semantic replay evidence        = 218 paths
```

Source/runtime construction evidence is retained separately and is never promoted to semantic behavior proof.

## Upstream V2 model/runtime-target inconsistency

Pinned-Forge execution exposed a structural inconsistency in the inherited WS26 V2 path model: four assigned paths map an exact `SVar` with `Mode$ Continuous` to `forge.game.trigger.TriggerHandler#parseTrigger`. Pinned Forge's `TriggerType` parser rejects `Continuous` as a trigger type.

Affected V2 paths:

- `forge-behavior-v2:452495ff67d15f9989748411f5ec41067e039c7b`
- `forge-behavior-v2:6dfbc7e6fb17a15e4445462f4383e6ebcf7ffedf`
- `forge-behavior-v2:7caaed2bb9b0c5fe0f5dab44de04175ec1867a16`
- `forge-behavior-v2:beee69a372f7b75417aa7fd9552cdfe6fae1a519`

This is recorded as `UPSTREAM_MODEL_FIX_REQUIRED = TRUE`. WS29 does not patch the immutable WS26 model and does not fabricate a parser binding to make these paths pass. It is not currently classified as a Forge shared-rules-core defect, so `SHARED_CORE_FIX_REQUIRED = FALSE`.

## Historical evidence compatibility

The 11 historical WS17 witnesses remain `INVALIDATED_BY_MODEL_CHANGE` under WS26 compatibility adjudication. They are not inherited as V2 PASS evidence.

WS27 is also fail-closed and therefore supplies no family-wide authoritative decision PASS that could close WS29's 218 decision-required paths. Cross-family architecture evidence remains supporting evidence only.

## Rules authority

Semantic adjudication uses the official Magic Comprehensive Rules effective `2026-08-07`, including the relevant continuous-effect, layer, copy, cleanup and player-control rules (`611`, `613`, `707.2`, `514.2`, `723`). Rules references establish authority; they do not convert unexecuted paths to PASS.

## Machine-readable outputs

The final immutable WS29 workflow artifact must contain:

- `WS29_WITNESSES.jsonl`
- `WS29_PATH_COVERAGE.json`
- `WS29_CONTINUOUS_EFFECT_INVENTORY.json`
- `WS29_COPY_CONTROL_INVENTORY.json`
- `WS29_RULES_ADJUDICATION.json`
- `WS29_GATE.json`
- `WS29_HASHES.sha256`
- `WS29_CASES.jsonl`
- `WS29_CASES_SUMMARY.json`
- `WS29_PROVENANCE.json`
- source-binding probe log, exit code and Surefire report
- `WS29_SOURCE_BINDING_TRACE.jsonl` when the probe reaches complete trace emission

`WS29_HASHES.sha256` covers the six required terminal WS29 machine outputs. The workflow verifies those hashes before artifact upload.

## Failure semantics

A source-binding test failure reached through the actual pinned-Forge TestNG fixture is retained as negative qualification evidence and does not prevent terminal fail-closed materialization. Compile, checkout, pin, boundary, artifact-integrity, case-materialization, or test-infrastructure failures still fail the workflow and therefore cannot masquerade as a completed qualification.

No silent fallback, card-name production hack, direct effect-resolution bypass, blanket WS17 inheritance, or global Q6 adjudication is permitted.

## Integration consequence

Consume WS29 as a **completed fail-closed workstream**, not as a qualified family PASS. Preserve all 301 semantic paths as UNKNOWN until later actual-card semantic executions satisfy the WS26 V2 witness ABI, and repair/re-adjudicate the four upstream model/runtime-target mismatches before attempting source-binding promotion for those paths.
