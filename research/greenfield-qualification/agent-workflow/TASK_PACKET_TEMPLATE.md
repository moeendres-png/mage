# Commander Simulator Next — Standard Task Packet Template

Use this file to prepare substantial Codex work. Fill all material fields; write `N/A` only when genuinely not applicable.

```text
TASK_ID =
MODEL_ROUTE = LUNA | TERRA | SOL_CODEX
PLANNER_ROUTE = NORMAL_SOL | EXISTING_ADJUDICATED_PLAN
REPOSITORY = moeendres-png/mage
AUDIT_BASE_SHA =
EXPECTED_TREE =
TARGET_BRANCH =
FORGE_PIN =

GOAL =

WHY_THIS_TASK =

ROOT_CAUSE_CLASS =
P_CLASS = P0 | P1 | P2 | P3 | P4 | P5 | N/A
CURRENT_EVIDENCE_CLASS =

IN_SCOPE =
OUT_OF_SCOPE =

OWNED_FILES_OR_SUBSYSTEMS =

DEPENDENCIES =

SOURCE_TRUTH_TO_VERIFY =
- HEAD
- TREE
- RUN
- JOB
- ARTIFACT
- ARTIFACT_DIGEST
- external pins

RULES_REFERENCES =

KNOWN_EVIDENCE =

IMPLEMENTATION_PLAN =
1.
2.
3.
4.

FORBIDDEN_SHORTCUTS =
- no card-name production hacks
- no pilot-side legality
- no silent first/default/random/pass/cancel fallback
- no manual outcome injection
- no direct effect/subability shortcut around required production parent path
- no unauthorized global registry or coverage mutation
- no PASS inheritance without compatible current evidence
- no weakening assertions merely to obtain a green workflow

HIDDEN_INFO_REQUIREMENTS =

RNG_REPLAY_REQUIREMENTS =

FAILURE_SEMANTICS =

TEST_PLAN =
1.
2.
3.

VALIDATION_COMMANDS =

PASS_CRITERIA =

NEGATIVE_CRITERIA =

EVIDENCE_OUTPUTS =

HANDOFF_REQUIREMENTS =
- final branch HEAD
- final TREE
- commands actually executed
- test outcomes
- run/job/artifact/digest where applicable
- exact evidence classification
- remaining UNKNOWN/PARTIAL/FAIL status
- blockers
- exact next action if incomplete

DEFINITION_OF_DONE =
```

## Implementation worker preamble

Prepend this block to a completed packet when sending it to Codex Terra or Sol:

```text
Execute the entire bounded task to semantic completion. Do not repeat already-valid qualification merely for reassurance. Before writing, verify the exact source identities listed in the packet. If the supplied base no longer matches, fail closed and report the mismatch rather than silently rebasing.

Rules Core authority, principal-scoped hidden information, explicit RNG, semantic replay, failure-category separation, evidence classifications, and workstream branch ownership are mandatory repository invariants.

Repair systemic defects generically. An UNKNOWN path is not evidence of an engine defect. Do not mutate canonical coverage unless this packet explicitly owns a serially authorized promotion step.

Treat execution as interruptible: persist material progress, reproducible commands, evidence, and handoff state to the task branch.
```

## Luna preamble

Use this stricter block for Luna:

```text
This is mechanical follow-up only. The underlying semantics are already fixed. Do not redesign rules, legality, cost/mana, targets, trigger/replacement/layer behavior, hidden information, RNG/replay, failure semantics, or effective-path identity. Do not weaken tests.

If completion requires a semantic change, stop the modification and report:
NEEDS_TERRA_OR_SOL_ANALYSIS = TRUE
with the exact file/contract that caused escalation.
```

## Review packet

For important Terra changes, use this adversarial Sol review shape:

```text
REVIEW_RESULT = PASS | FIX_REQUIRED | REQUALIFICATION_REQUIRED

Check:
- Rules Core authority vs pilot/adapter heuristics
- production-parent witness reachability
- exact current path/model identity
- hidden-information leakage
- RNG/replay determinism
- failure-category correctness
- generic-vs-card-specific implementation
- multiplayer/Commander assumptions
- blast radius against prior PASS evidence
- official Magic rules where semantic adjudication is required

Return:
BLOCKERS =
HIGH =
MEDIUM =
LOW =
REQUIRED_FIXES =
REQUIRED_RETESTS =
PASS_EVIDENCE_INVALIDATED = TRUE/FALSE/UNKNOWN
```
