# WS33 AF8 — Evidence Contract Repair — Terra Task Packet

## Routing

```text
TASK_ID = WS33-AF8-EVIDENCE-CONTRACT-REPAIR-20260908
MODEL_ROUTE = TERRA
PLANNER_ROUTE = NORMAL_SOL
REPOSITORY = moeendres-png/mage
AUDIT_BASE_SHA = 6da237b704ba5e66c58c2334f47e36ef68ca980d
EXPECTED_TREE = 8f6d0151e4a9095c95925d6f6065214d382bf1dc
TARGET_BRANCH = work/ws33-af8-evidence-contract-repair-20260908
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ROOT_CAUSE_CLASS = QUALIFICATION_EVIDENCE_CONTRACT_MISMATCH
P_CLASS = P2
CURRENT_EVIDENCE_CLASS = DIRECTLY_VERIFIED + CODE_DERIVED
```

## Goal

Close exactly the current AF8 fail-closed decision-attribution blocker without weakening the inherited WS31/WS33 decision-evidence contract and without changing Magic rules semantics.

Current terminal symptom:

```text
DECISION_ID 'a-rest-svar-af8-alternatives-1-remote' missing path_id
```

The repair must establish the semantic role and producer of that decision before changing validation behavior.

## Frozen evidence

Latest terminal AF8 evidence consumed by this task:

```text
RUN = 34165574477
JOB = 101875828886
SOURCE_HEAD = 6120ca3ee9754cbad4600ee45008ee2455b95465
SOURCE_TREE = 264e881c43c643363f0a499764c0a81ae8285c4e
ARTIFACT_ID = 10034108017
ARTIFACT_NAME = ws33-abc-a-rest-svar-af8-34165574477
ARTIFACT_DIGEST = sha256:5e300282cbfab475d4291b072b1c12c19ac29b64843e93b4d5cc8676b36bcf49
```

Observed run stages:

```text
Record = SUCCESS
Replay = SUCCESS
Fail-closed AF8 adjudication = FAILURE
Always-run evidence seal = SUCCESS
Artifact upload = SUCCESS
```

Current canonical retained coverage before this task:

```text
TOTAL = 4188
PASS = 488
UNKNOWN = 3700
A_UNKNOWN = 57
B_UNKNOWN = 675
C_UNKNOWN = 700
D_UNKNOWN = 920
E_UNKNOWN = 1029
F_UNKNOWN = 319
G_UNKNOWN = 0
H_UNKNOWN = 0
```

This task does not own coverage promotion.

## What is already established

The current strict reader in:

`research/greenfield-qualification/actual-card-behavior/ws33/ws33_decision_path_evidence.py`

allows null path only for explicit setup decisions (`STARTING_PLAYER`, `MULLIGAN`) and rejects unattributed non-setup decisions.

The AF8 adjudicator consumes that reader and requires exact path coverage for all eight expected AF8 paths.

The AF8 hardener:

`research/greenfield-qualification/actual-card-behavior/ws33/ws33_harden_a_rest_svar_af8_runtime.py`

binds observation-only callbacks but does not introduce a path-id-specific decision policy. It asserts:

```text
WS33_A_SVAR_AF8_RULES_MUTATION=0 card_name_branch=0 path_id_branch=0
```

The AF8 campaign enters the production cast/payment route through `PlaySpellAbility.playSpellAbility`, uses Forge-generated options, and Record/Replay already complete successfully.

The remote transport barrier introduced by `apply-ws33-input-confirm.py` is explicitly payload-free and is not a pilot/rules decision. Do not conflate that transport acknowledgement with the failing decision-tape row.

## In scope

1. Reproduce/locate the exact producer of decision ID `a-rest-svar-af8-alternatives-1-remote` in the generated AF8 harness/runtime stack.
2. Determine whether that event is:
   - a genuine discretionary gameplay decision belonging to one of the eight active AF8 paths; or
   - a non-discretionary auxiliary/setup/protocol event that should not count as path behavior evidence.
3. Repair the producer/contract at the narrowest correct boundary.
4. Add focused regression tests proving the intended attribution rule.
5. Run focused parser/hardener/adjudicator tests and the full AF8 Record/Replay workflow on this repair branch if the available execution environment permits it.
6. Produce a terminal handoff with exact evidence and no coverage promotion.

## Out of scope

- changing canonical WS33 coverage;
- requalifying G or H;
- generic Forge Rules-Core repair without new evidence;
- changing legal option generation;
- changing target legality, mode legality, mana/cost legality, stack semantics, or resolution outcomes;
- card-name/path-name special cases;
- weakening exact Record/Replay comparison;
- allowing arbitrary null-path decisions;
- architecture freeze work.

## Owned files/subsystems

Primary ownership is limited to AF8 qualification/evidence wiring and tests, especially:

```text
research/greenfield-qualification/actual-card-behavior/ws33/ws33_decision_path_evidence.py
research/greenfield-qualification/actual-card-behavior/ws33/test_ws33_decision_path_evidence.py
research/greenfield-qualification/actual-card-behavior/ws33/ws33_harden_a_rest_svar_af8_runtime.py
research/greenfield-qualification/actual-card-behavior/ws33/ws33_adjudicate_a_rest_svar_af8.py
research/greenfield-qualification/actual-card-behavior/ws33/ws33_prepare_g_ability_harness.py
research/greenfield-qualification/actual-card-behavior/ws33/ws33_adapt_g_svar_af_harness_to_a_af8.py
research/greenfield-qualification/actual-card-behavior/ws33/runtime-overlays/**
.github/workflows/ws33-abc-a-rest-svar-af8-runtime.yml
```

Modify only the subset proven necessary by source inspection.

## Mandatory source-truth gate

Before writing:

```text
verify HEAD == 6da237b704ba5e66c58c2334f47e36ef68ca980d or explicitly document any task-branch commits on top
verify base TREE == 8f6d0151e4a9095c95925d6f6065214d382bf1dc
verify FORGE_PIN == 8c7e9afb8e6caee88644b94e25da5852e36f8928
verify current AF8 workflow and strict reader source
verify frozen failed run/job/artifact/digest above
```

Do not silently rebase to a newer canonical branch.

## Required root-cause investigation

Trace the failing decision end-to-end:

```text
Forge authoritative choice construction
→ PlayerControllerHuman external-decision request
→ remote principal/client transport if any
→ ExternalDecisionTape event
→ harness currentPath/path attribution capture
→ decision-events-with-path.tsv
→ ws33_decision_path_evidence.py
→ AF8 adjudicator
```

Identify the exact point at which `path_id` becomes null and why.

Do not infer semantics from the decision ID suffix `-remote` alone.

## Repair decision tree

### Case A — genuine discretionary gameplay decision

If the event asks the pilot to select among authoritative gameplay alternatives/options during an active AF8 case, then `path_id` is mandatory.

Repair the producer/attribution boundary so the event is recorded under the active exact AF8 path.

Requirements:

- no inferred legality;
- no fabricated path from card name, decision ID text, or option text;
- use the already authoritative active campaign/path identity;
- actor/principal must remain exact;
- replay must consume the same semantic event under the same path.

### Case B — non-discretionary auxiliary/setup/protocol event

Only if source/runtime evidence proves the event is not a gameplay choice may it remain outside behavior-path coverage.

Do **not** implement a broad rule such as:

```text
if decision_id.endswith("-remote"): allow null path
```

Instead add an explicit, typed, semantically justified auxiliary classification at the producer or evidence ABI boundary. The validator must allow only the enumerated non-gameplay class, just as current setup exceptions are explicit.

Gameplay decision kinds with null path must continue to fail closed.

If an auxiliary event is recorded in the decision tape for replay ordering, it must remain deterministic and must not be counted as behavior-path evidence.

## Forbidden shortcuts

- no `*-remote` suffix whitelist;
- no card-name whitelist;
- no path-ID whitelist;
- no ignoring all null-path events;
- no removal of the null-path rejection test;
- no accepting a decision solely because Record and Replay match;
- no changing expected eight-path set;
- no direct target/mode/cost injection;
- no pilot-side legality reconstruction;
- no manual outcome injection;
- no coverage promotion.

## Focused regression tests

At minimum, prove all applicable cases:

1. explicit setup null-path decisions remain accepted only under existing setup semantics;
2. a null-path gameplay target/mode/entity/discrete decision is rejected;
3. a correctly path-attributed AF8 gameplay decision is counted for the exact expected path;
4. foreign path remains rejected;
5. actor/principal mismatch remains rejected;
6. duplicate principal/event remains rejected;
7. rejected/failed decision remains rejected;
8. if an auxiliary class is introduced, only that explicit class is accepted and it contributes zero behavior-path counts;
9. malformed/forged auxiliary classification fails closed;
10. Record/Replay decision-path counts remain equal;
11. all eight AF8 expected paths remain covered exactly as required.

## Validation

Focused source tests:

```bash
python -m py_compile \
  research/greenfield-qualification/actual-card-behavior/ws33/ws33_decision_path_evidence.py \
  research/greenfield-qualification/actual-card-behavior/ws33/ws33_harden_a_rest_svar_af8_runtime.py \
  research/greenfield-qualification/actual-card-behavior/ws33/ws33_adjudicate_a_rest_svar_af8.py

cd research/greenfield-qualification/actual-card-behavior/ws33
python -m unittest -v test_ws33_decision_path_evidence.py
```

Then execute the branch-equivalent AF8 Record/Replay workflow against the pinned Forge runtime. Preserve the existing checks that prohibit direct `sa.resolve()`, target injection, direct effect entry, or payment bypass.

If GitHub Actions cannot be dispatched on the repair branch without changing workflow trigger policy, do not weaken the workflow solely to obtain a run. Persist the exact executable command/patch and report the CI-dispatch limitation; integration can execute it on the serial canonical promotion step.

## Pass criteria

This task is technically complete only when:

- exact producer/semantic role is established;
- the attribution contract is repaired at the correct boundary;
- strict null-path gameplay rejection remains;
- focused tests pass;
- full AF8 Record and tape-driven Replay pass when execution is available;
- fail-closed AF8 adjudication passes when execution is available;
- decision/event and RNG/effect/observation/play-stage replay comparisons remain intact;
- no Magic rules behavior was changed by the qualification fix;
- no coverage is promoted on this branch;
- terminal evidence and exact identities are persisted.

## Failure semantics

Do not label the current defect `ENGINE_FAILURE` or `CARD_BEHAVIOR_FAILURE` unless new execution evidence independently establishes those conditions.

Default unresolved classification remains:

`QUALIFICATION_EVIDENCE_CONTRACT_MISMATCH`

If source inspection proves a different class, document the evidence before changing classification.

## Definition of Done / handoff

Persist:

```text
FINAL_HEAD =
FINAL_TREE =
ROOT_CAUSE =
DECISION_SEMANTIC_ROLE = GAMEPLAY_DISCRETIONARY | AUXILIARY_NONDISCRETIONARY | OTHER
PATH_ID_NULL_ORIGIN =
FILES_CHANGED =
TESTS_RUN =
TEST_RESULTS =
AF8_RUN =
AF8_JOB =
AF8_ARTIFACT =
AF8_ARTIFACT_DIGEST =
COVERAGE_MUTATED = FALSE
COVERAGE_PROMOTED = FALSE
EVIDENCE_CLASS =
SOL_REVIEW_REQUIRED = TRUE
SOL_CODEX_REQUIRED = FALSE unless P0/P3/P5 or repeated hard Terra failure becomes directly evidenced
```

Do not claim WS33 COMPLETE from this task alone.