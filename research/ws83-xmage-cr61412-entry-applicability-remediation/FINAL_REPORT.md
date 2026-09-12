# WS83 Final Report — XMage CR 614.12 Entry-Applicability Remediation

## Verdicts

- SOURCE_LOCK = PASS (aeaa7214 / d5bd67ab; accepted ancestor 7135d5e5 unchanged)
- AUTHORITY_LOCK = PASS (CPL main 79c5af1f / tree 2026c4c3; corrected cases + adjudication)
- WS81_FAILURE_REPRODUCED = PASS (pre-fix 3 run, 1 failure: A red with forbidden prompt)
- READ_FIRST_XHIGH_ADJUDICATION = PASS (read/test-first, no production edits before verdict)
- ROOT_CAUSE_SYSTEMICALLY_IDENTIFIED = PASS (ENGINE_DEFECT at earliest applicability boundary)
- CARD_NAME_HACKS = 0 (no Clone/Humility strings, no H01 branches; one comment mention only)
- SECOND_RULES_ENGINE = 0 (reused layer-6 apply logic; no parallel engine)
- XMAGE_H01_A_HUMILITY_FIRST = PASS (no decision, no copy, 1/1, then 0/0 -> SBA)
- XMAGE_H01_B_CLONE_FIRST = PASS (decision + Bear copy retained 2/2)
- XMAGE_H01_C_NO_HUMILITY = PASS (normal copy 2/2)
- XMAGE_H01_CORRECTED_REQUALIFICATION_ON_SUCCESSOR = PASS
- DECISION_OCCURRENCE_DISCRIMINATOR = PASS
- POST_HUMILITY_DISCRIMINATOR = PASS
- ACTUAL_CARD_COVERAGE = PASS
- RELEVANT_REGRESSIONS = PASS
- ENGINE_PIN_CHANGE = 0
- BEHAVIOR_CREDIT_CHANGE = 0
- SUCCESSOR_ACCEPTED = NO
- FULL107_BEHAVIOR = NOT_RUN
- ARCHITECTURE_FREEZE = NOT_CLAIMED
- PRODUCTION_PROVIDER = NOT_SELECTED

## What was done

1. Locked source (aeaa7214 WS81 evidence base) and CPL authority (79c5af1f) read-only.
2. Invoked Foundry adjudicator at XHIGH read-first (no edits); persisted verdict that the
   earliest systemic boundary is `ContinuousEffects.getApplicableReplacementEffects`, that no
   future-state facility exists, and that no authority gate blocks a bounded repair.
3. Reproduced the WS81 family pre-fix (A=FAIL forbidden prompt, B/C=PASS).
4. Implemented the smallest systemic repair in `ContinuousEffects` (+ comment in
   `ReplacementEffectImpl`): self-scope entering replacements are excluded when the source
   ability would not survive pre-existing layer-6 `LoseAbility` effects, evaluated by reusing
   each remover's own `apply` filter logic against the entering permanent temporarily exposed
   to battlefield queries. Fail-closed, reentrancy-guarded, filter-precise.
5. Added `WS83CR61412SystemicTest` (Phantasmal Image suppress, Vesuva preserve, Clone/Dress Down
   suppress) using real cards on the same general machinery.
6. Requalified fresh: WS81 3/3, WS83 systemic 3/3, Clone 7/7, Humility 1/1, Vesuva 2/2,
   PhantasmalImage 21/21, combined 16/16 — all green with MAVEN_OPTS tmpdir workaround for a
   full /tmp filesystem (no repo impact).

## Tests / evidence

- New: WS83CR61412SystemicTest (3 tests, DIRECTLY_VERIFIED).
- Preserved: WS81H01CorrectedTest (3 tests, historical red unmodified, now freshly green).
- Regressions: CloneTest, HumilityTest, VesuvaTest, PhantasmalImageTest (all DIRECTLY_VERIFIED).
- Package: research/ws83-xmage-cr61412-entry-applicability-remediation/{SOURCE_LOCK,ROOT_CAUSE,
  ARCHITECTURE_ADJUDICATION,IMPLEMENTATION,VALIDATION.json,FINAL_REPORT}.md
- Env note: Maven builds require `MAVEN_OPTS="-Djava.io.tmpdir=/home/moeen/tmp/opencode"`
  + `TMPDIR=...` because the host /tmp tmpfs is full (7 GB stale); no source impact.

## Remaining blockers

- None for the assigned systemic scope. Coordinator adjudicates successor acceptance separately.

## Dependencies unblocked

- Coordinator can consume: validated technical successor commit, per-case PASS/FAIL, systemic +
  negative-control evidence, hard-gate table.

## Exact Next Action

- Commit the bounded technical successor, dry-run + actual canonical safe_push to
  ws83/xmage-cr61412-entry-applicability-remediation-20260912, verify remote/local HEAD equality.
