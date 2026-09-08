# WS33-C pilot run PENDING

RUN = 34288650019
EVENT = push (branch push registered the run; duplicate dispatch 34288689666 cancelled)
WORKFLOW = WS33-C AbilitySub pilot (production-parent witness)
WORKFLOW_FILE = .github/workflows/ws33-c-abilitysub-pilot.yml
SOURCE_HEAD = a2aa88e5471c6ab414b8e04f8e7f6bbaaa098ec4
SOURCE_TREE = db62be9d19194e2a187f860d8c8da844be3b0d8b
AUDIT_BASE_SHA = 895240f4058076764227a418ad28e84f61d3a7ed
AUDIT_BASE_TREE = cec73ae51b0168280ea648892f3e9edd46dcd883
BRANCH_ADVANCE_NOTE = Source advanced by two branch-owned commits since audit
lock (ada567e664 manifest+harness, a2aa88e547 pilot workflow). No unrelated
content: 9 files, all under `c-campaign/`, `checkpoints/`, `.github/workflows/`.
Canonical coverage untouched.
FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928
EXPECTED_ARTIFACT = ws33-c-abilitysub-pilot-34288650019
EXPECTED_CASES = 1 (forge-behavior-v2:b42b594f2523a243cf1b4877de9612a831bb71f6 via Cloudblazer)
EXPECTED_GATE = generated/evidence/WS33_C_PILOT_GATE.json with status PASS
IMMUTABLE_DEPS = owned manifest b47510017fbfd5cae478917c37f83c1a41e73095eb49a2fa9ecb43360c809ca4;
queue a88842375e5e91894acb238c6306a60760dc77d0f098e5dbbd2069e2dbca1482;
overlay runtime-overlays/apply-ws33-svar-reachability.py (validated at pin on scratch)
COVERAGE_PROMOTION = FALSE
COVERAGE_MUTATED = FALSE (asserted in-workflow)
FREEZE = Run source frozen at SOURCE_HEAD/SOURCE_TREE above. WRITE_FREEZE on
c-campaign harness inputs until terminal status.

Terminal adjudication will persist PASS or FAIL (with root-cause class)
before any repair. Evidence classification for run/job/artifact metadata:
DIRECTLY_VERIFIED on read-back.

TURN_STATUS = INTERRUPTED
TASK_COMPLETE = NO
