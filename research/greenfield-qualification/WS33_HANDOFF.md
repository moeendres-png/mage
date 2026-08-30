# WS33 — Q6 Systemic Runtime Closure, ABI V2.1 & Integrated Actual-Card Campaign

WORKSTREAM_COMPLETE = FALSE
WS33_MODEL_ERRATA_GATE = PASS
WS33_WITNESS_ABI_V2_1_GATE = PASS
WS33_ACTUAL_CARD_CAMPAIGN = FAIL_CLOSED

ACTION_COST_DECISION = FAIL_CLOSED
TRIGGER_REPLACEMENT_ZONE_SBA = FAIL_CLOSED
CONTINUOUS_COPY_CONTROL = FAIL_CLOSED
COMBAT_COMMANDER = FAIL_CLOSED
HIDDEN_RNG_REPLAY = FAIL_CLOSED

Q6_CANDIDATE_FOR_CROSS_QUALIFICATION = FALSE
WS32_COMPATIBILITY = NOT_RUN
WS34_ELIGIBLE = FALSE

Q6_ACTUAL_CARD_BEHAVIOR_CANONICAL = NOT_ADJUDICATED_BY_WS33
FAILURE_SEMANTICS_CANONICAL = NOT_ADJUDICATED_BY_WS33

WS13_ELIGIBLE = FALSE
INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE
READY_FOR_GREENFIELD_BUILD = FALSE
PRODUCTION_REPOSITORY_CREATED = FALSE

## Evidence boundary

- WS33 evidence-source commit: `bdbaef27d410797fc853133a4994eaac68cb1232`
- WS33 evidence-source tree: `32075d48ae5e8376369d37431e8024865c8b2663`
- Exact WS26 ancestry: `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef` / tree `837f445f78bb26462653c58baf1532e294151b10`
- Exact Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Qualified runtime anchor: `55820618e7243bd5ba8cfa33c3148cea8c166c73` / tree `3706900d49c6ef61690c227bb7b4c0067fbcfb44`
- Runtime overlay digest: recorded in `WS33_RUNTIME_OVERLAY_MANIFEST.json`; materialization status is `NOT_EXECUTED`, so it is not candidate-runtime proof.
- Final publication HEAD/TREE and workflow run/job/artifact/digest: pending the authoritative WS33 workflow. The workflow uploads evidence even when the candidate hard gate fails.

## Consumed immutable predecessors

| Workstream | HEAD | Run | Artifact | Digest |
|---|---|---:|---:|---|
| WS26 | `206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef` | 33283478862 | 9723722686 | `sha256:b9e1fc4fd792b0baa1da1c17e3bbc9e01b2557d4b73b8590e680679f53b59883` |
| WS27 | `3f42def33d25c7f03f4a2b612ac1cce129180e7c` | 33304817385 | 9730143001 | `sha256:e8b8a690161c464599269cbd7caed0680291f35428163c6e43c5fe3f71d592be` |
| WS28 | `56977228b7fc0d149aa3719f5f2a9837e59c63a2` | 33311668709 | 9732209789 | `sha256:e96df123f562773f5dc7e3495ea41c30183d62aed9a829ca5f2668a954fa1eaa` |
| WS29 | `ca5fd0166c9a3c7030f37975f0d82380acaf6f8a` | 33312384946 | 9732414644 | `sha256:b30415583c2b8c16c6b7cc523e69f5241922aa34d0d3fff17af942dba9c87f62` |
| WS30 | `b5bc3803ca04e37bd9223e3505e4a748ce03404c` | 33316769544 | 9733716966 | `sha256:9bd386e63983b8d20ea3a2901bd2cdf351c5914ad2379c51477da6fb4987e2ab` |
| WS31 | `acd6ae330e798f0e2081d194b371f1d66310aab2` | 33318196568 | 9734159178 | `sha256:d1af7b9c348af2a56ebf9b398d29f06d0f2794df089bdd3caa4b18ebf471cffc` |
| WS32 | `6ca2a7bbacd074cc84fa4a6019c4d26e5e3717a9` | 33316168298 | 9733547137 | `sha256:6eb2f0078bf8473571b10433211957e44ef3af93b7bf233e1072e7e12364578e` |

## Model and ABI results

- Raw WS26 path count: 4,280.
- Effective post-erratum production-required path count: 4,276.
- Effective family counts: ACTION_COST_DECISION 2,697; TRIGGER_REPLACEMENT_ZONE_SBA 1,174; CONTINUOUS_COPY_CONTROL 297; COMBAT_COMMANDER 27; HIDDEN_RNG_REPLAY 81.
- The four WS29 aliases remain as deprecated historical provenance. Exact pinned source and dataflow prove `AddStaticAbility` → `AbilityUtils.getSVar` → `Card.getStaticAbilityForStaticAbility` → `StaticAbility.create` → `StaticAbilityMode.Continuous`; they are not independent `TriggerHandler#parseTrigger` behavior paths.
- ABI V2.1 retains the WS26 semantic contract and adds successor ancestry, immutable WS26 model hash, explicit effective-model hash, declared overlay hash, patched-Forge digest, and execution-environment identity.
- Positive inherited and successor fixtures pass. All 17 negative fixtures are rejected for their intended reason.

## Admission results

- WS26/WS28: the same two canonical WS16-derived paths are `ABI_ADMISSIBLE` and are not rerun.
- WS27 Swiftwater Cliffs: `REEXECUTION_REQUIRED`; its assertions omit expected/actual values, primitive exercise is absent, and its decision-boundary value is outside ABI V2.1.
- WS29: four records are `MODEL_ERRATUM`; no semantic PASS is inherited.
- WS30: all 27 local family records are `REEXECUTION_REQUIRED`; each lacks the integrated ABI state/trace/parent-lifecycle shape, and tape-required paths also lack the corresponding evidence.
- WS31: all 81 paths remain `NONQUALIFYING_DIAGNOSTIC`; the artifact reports missing decision tapes and 1,970 unauthorized private exposures.
- WS32: rejected as a Q6 witness source and retained only as a compatibility dependency.

## Integrated campaign state

- Path status: PASS 2; FAIL 0; UNSUPPORTED 0; UNKNOWN 4,274.
- Identity reconstruction: FULL 0; PARTIAL 1,678.
- Decision/RNG/Hidden/Replay complete PASS evidence added by WS33: 0/0/0/0. The two admitted paths require none of these tapes.
- Implementation targets: 203; evidence-profile scenario groups: 249; missing scenario-template groups: 247.
- Highest-fanout open targets are `TargetRestrictions`, `Cost`, `AbilitySub`, `AbilityUtils#calculateAmount`, `ChangeZoneEffect`, and `TriggerChangesZone`.
- No parser/source-presence result, predecessor-local PASS, or global Q1/Q2/Q3 result was promoted to behavior PASS.
- Card-name production hacks: 0. Second pilot Rules Engine: 0. Silent fallback count: 0. Stdout-only PASS count: 0.

## Runtime and compatibility state

- Runtime production changes made by WS33: none. WS33 currently adds qualification-only model, ABI, registries, validators, and workflow code.
- Q1/Q2/Q3/Q4/Q5/Q7: `NOT_INVALIDATED` by the qualification-only changes.
- WS32: `FOCUSED_REQUALIFICATION_REQUIRED` after one common candidate overlay is materialized. The standalone WS32 PASS has not been relabeled as integrated compatibility.

## Remaining blockers and next action

The machine-listed blockers are `MISSING_SCENARIO_TEMPLATE` for 4,274 effective paths, `INTEGRATED_RUNTIME_OVERLAY_NOT_EXECUTED`, and `WS32_COMPATIBILITY_NOT_RUN`. These are still actionable inside WS33, so this handoff intentionally does not claim fail-closed workstream completion.

Next action: materialize the declared WS01/Q2/Q3/WS32 overlay set at the exact Forge pin, execute implementation-target-first shards beginning with ACTION_COST_DECISION, attach the required decision/RNG/hidden/replay evidence, repair only proven systemic runtime defects, and then run the focused WS32 compatibility controls on the same overlay digest.

Internal artifact hashes are in `actual-card-behavior/ws33/WS33_HASHES.sha256`.
