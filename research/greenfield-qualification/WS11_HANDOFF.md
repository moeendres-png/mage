# WS11 handoff

WORKSTREAM_COMPLETE: `FALSE` (hard gate remains fail-closed)

BRANCH: `work/ws11-actual-card-semantic-closure-20260829`

BASE_SHA: `624c0a652de775dcdf9d641438b5c18ef4ce50d2`

QUALIFIED_HEAD: `a604db2f8ebedfa9fad32fe71425ea2bfd031ec4`

QUALIFIED_TREE: `3c5d1337a30f14fc9cf61e708c0178bd24179102`

FILES_CHANGED:

- `.github/workflows/ws11-actual-card-semantic-closure.yml`
- `research/greenfield-qualification/WS11_ACTUAL_CARD_SEMANTIC_GATE.json`
- `research/greenfield-qualification/WS11_ACTUAL_CARD_SEMANTIC_GATE.md`
- `research/greenfield-qualification/actual-card-behavior/WS11_BEHAVIOR_PATH_MODEL.md`
- `research/greenfield-qualification/actual-card-behavior/WS11_WITNESS_REGISTRY.json`
- `research/greenfield-qualification/actual-card-behavior/test_ws11_qualify.py`
- `research/greenfield-qualification/actual-card-behavior/ws11_qualify.py`

DEPENDENCY_HEADS:

- WS90 final: `624c0a652de775dcdf9d641438b5c18ef4ce50d2`
- WS02 corpus: integrated unchanged; exact known identities `1678`, explicit unknown real-opponent slots `142`, synthetic promotion `false`
- rejected WS10 evidence input run: `33247342048` (loadability/source input only; no behavior PASS inherited)
- Forge: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

TESTS:

- `py -3 -m unittest discover -s research/greenfield-qualification/actual-card-behavior -p 'test_ws11_*.py' -v`: PASS, 5/5
- exact local materialization from the WS10 artifact and pinned Forge: completed with expected fail-closed exit 3
- per-identity rows: 1678
- workflow `33251464459`: PASS (the green run proves evidence materialization and honest fail-closed enforcement, not Q6 PASS)
- per-identity artifact SHA-256: `1f46fc66d2049d65c7ede91700c0e76e38b3fb7c49c13bb394dd20aa6ea8ced7`
- per-identity concrete evidence refs: `33251282186 / 99097271546 / 9714450822 / sha256:a9505ece9e893a51c535a2674626a59d9c78be7a5cee3c31b4bd5239964f1f42`; null-reference rows: `0`

RUN_IDS: `33251282186`, `33251464459`

JOB_IDS: `99097271546`, `99097754070`

ARTIFACT_IDS: `9714450822`, `9714505392`

ARTIFACT_DIGESTS: `sha256:a9505ece9e893a51c535a2674626a59d9c78be7a5cee3c31b4bd5239964f1f42`, `sha256:74be5debf765e76d3aa8ab8a868795193b8f5dc6b4856d95bf9e94b087a7d581`

EVIDENCE_CLASSES: `CODE_DERIVED`, `TECHNICALLY_CONFORMANT`, `UNKNOWN`

Q6 result: `FAIL`

Coverage counts: `FULL=0`, `CONDITIONAL_FULL=0`, `PARTIAL=1678`, `UNKNOWN=0`, `UNSUPPORTED=0`

Behavior-signature count: `1677`

Dedicated scenario count: `0`

Cross-rule divergences: `0` (no semantic witness asserted; no engine-majority adjudication performed)

Card-name production hacks: `0`

Global WS01/WS05/WS06 PASS inheritance rows: `0`

BLOCKERS:

- All 1,677 exact Forge behavior-path signatures reached by the 1,678 identities lack executable, engine-state-asserting witnesses bound to those exact signatures.
- Consequently all 1,678 production-required identities are `PARTIAL`; construction and exact source mapping are retained only as prerequisites.

NEXT_ACTION: Add reusable systemic semantic probes keyed by exact behavior-path signature, retain immutable traces and state assertions, adjudicate meaningful semantics against official Magic/Commander rules, and rerun only affected signatures. Do not start architecture freeze on this result.
