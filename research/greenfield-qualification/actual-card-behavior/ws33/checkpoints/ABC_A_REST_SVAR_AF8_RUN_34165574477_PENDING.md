# AF8 replacement run 34165574477 — PENDING

```makefile
STATUS=PENDING
COVERAGE_MUTATED=FALSE
COVERAGE_PROMOTION=FALSE
SOURCE_HEAD=6120ca3ee9754cbad4600ee45008ee2455b95465
SOURCE_TREE=264e881c43c643363f0a499764c0a81ae8285c4e
WORKFLOW=.github/workflows/ws33-abc-a-rest-svar-af8-runtime.yml
FORGE_PIN=8c7e9afb8e6caee88644b94e25da5852e36f8928
EXPECTED_PATH_COUNT=8
EXPECTED_PATH_SET_SHA256=10c3825fa3ba1e58aadcaacad1012263c4201438cf8c694db6cb10b3bae7b0f1
EXPECTED_ARTIFACT_NAME=ws33-abc-a-rest-svar-af8-34165574477
AF8_RUN=34165574477
AF8_JOB=101875828886
AF8_ARTIFACT=PENDING
AF8_ARTIFACT_DIGEST=PENDING
```

This source applies the persisted observation-only `apply-ws33-stack-resolution-reachability.py` and `apply-ws33-a-rest-play-stage-observer.py` overlays before harness compilation, and fail-closes on absence of the exact observer APIs. It repairs only run 34164631499's `QUALIFICATION_OVERLAY_DEPENDENCY_OMISSION`; no behavior evidence or coverage is inherited from that failed run.
