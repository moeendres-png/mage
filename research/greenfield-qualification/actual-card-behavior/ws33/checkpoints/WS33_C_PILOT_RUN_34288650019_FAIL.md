# WS33-C pilot run 34288650019 terminal FAIL (adjudicated)

RUN = 34288650019
JOB = 102269993167
JOB_CONCLUSION = failure (step "Apply exact Rules Decision Observation runtime stack")
SOURCE_HEAD = a2aa88e5471c6ab414b8e04f8e7f6bbaaa098ec4
SOURCE_TREE = db62be9d19194e2a187f860d8c8da844be3b0d8b
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
ARTIFACT = 10080495228 (ws33-c-abilitysub-pilot-34288650019, overlay logs only)
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE (no witness executed; canonical files untouched)

## What passed in the run (DIRECTLY_VERIFIED from run log)

- manifest binding (700 owned paths), pins (Forge + ws01/ws12/ws32/direct),
  all overlays incl. `WS33_SVAR_REACHABILITY_OVERLAY=PASS`.

## Root cause (HARNESS_ASSERTION_DEFECT, branch-owned workflow line)

Failing line (workflow, added in a2aa88e547):

```
grep -F 'AbilitySub.setWs33ResolutionObserver' forge/.../spellability/AbilitySub.java
```

The qualified name `AbilitySub.setWs33ResolutionObserver` never occurs in
the patched source. The overlay adds the declaration
`public static void setWs33ResolutionObserver(final Consumer<AbilitySub> ...)`
— the qualifier `AbilitySub.` exists only at call sites (e.g. the harness
test's `AbilitySub.setWs33ResolutionObserver(...)`), which is why the AF8
workflow greps the *test* file, not the patched source.

Local reproducer (pin file + branch overlay script, scratch only):
- qualified grep -> exit 1 (exact CI failure mode);
- unqualified `grep -F 'setWs33ResolutionObserver'` -> exit 0, one match
  (the setter declaration).

## Classification

- Failing layer: branch-owned CI verification line (harness infrastructure).
- NOT an engine defect, NOT an overlay defect (overlay applied correctly),
  NOT a model defect, NOT a witness-reachability defect.
- No production-reachable behavior implicated; no repair outside branch
  authority needed. No Sol escalation (no semantic/architecture question).

## Repair plan (minimal, systemic)

One-line workflow fix: probe the unqualified setter name in the patched
source (`grep -F 'setWs33ResolutionObserver' .../AbilitySub.java`), matching
what the overlay actually adds. Then push (re-triggers pilot run) and
adjudicate the replacement run from its own PENDING checkpoint.

EVIDENCED_PATH_COUNT = 0
REMAINING_UNKNOWN_COUNT = 700
ROOT_CAUSE_CLASSES = HARNESS_ASSERTION_DEFECT (workflow verification line)

## Exact next action

Commit this FAIL checkpoint, apply the one-line workflow fix, push, and
register the replacement run with a fresh PENDING checkpoint.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
