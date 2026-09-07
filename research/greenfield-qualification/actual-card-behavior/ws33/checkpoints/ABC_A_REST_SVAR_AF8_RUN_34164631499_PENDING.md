# AF8 replacement run 34164631499 — PENDING frozen qualification

```makefile
STATUS=PENDING
COVERAGE_PROMOTION=FALSE
COVERAGE_MUTATED=FALSE

SOURCE_HEAD=895240f4058076764227a418ad28e84f61d3a7ed
SOURCE_TREE=cec73ae51b0168280ea648892f3e9edd46dcd883
WORKFLOW=.github/workflows/ws33-abc-a-rest-svar-af8-runtime.yml
WORKFLOW_SHA=895240f4058076764227a418ad28e84f61d3a7ed
FORGE_PIN=8c7e9afb8e6caee88644b94e25da5852e36f8928

EXPECTED_PATH_COUNT=8
EXPECTED_PATH_SET_SHA256=10c3825fa3ba1e58aadcaacad1012263c4201438cf8c694db6cb10b3bae7b0f1
EXPECTED_ARTIFACT_NAME=ws33-abc-a-rest-svar-af8-34164631499

AF8_RUN=34164631499
AF8_JOB=101873135926
AF8_ARTIFACT=PENDING
AF8_ARTIFACT_DIGEST=PENDING
```

## Exact expected paths

```text
forge-behavior-v2:1ccbeda989a96da340b08186248977134c3bb7bc
forge-behavior-v2:7549c1671f9f56f576526e70d918fceedce03cfc
forge-behavior-v2:9c210fe6f626c37c9b3bdd9134a4bfc26dc74fd4
forge-behavior-v2:a31f4630c06971a5a9c4da7dc7dbef5ee8a8f7b4
forge-behavior-v2:b0d0351f7c2e451972cc5ed513ee0bd0c48a7e6a
forge-behavior-v2:f2a19455bb1e70147b0c06fd710e6325848e18e3
forge-behavior-v2:fa2b8db73866aee9b2f99fdfa6d3f1827063964e
forge-behavior-v2:feb15cc38af1b2d8ffb1f2f3cfe7deb42051aa2e
```

## Immutable route dependency re-verification

DIRECTLY_VERIFIED immediately before this checkpoint:

```makefile
ROUTE_RUN_ID=34063748962
ROUTE_ARTIFACT_ID=9998291348
ROUTE_ARTIFACT_DIGEST=sha256:646594434eb987009561127f012bd0d974dcec97e67bef0bf478294f1fd9d0e9
ROUTE_SOURCE_HEAD=48cb9a018f606f1209d14ee587a6ff3f14d263a1
OUTER_ZIP_SHA256=646594434eb987009561127f012bd0d974dcec97e67bef0bf478294f1fd9d0e9
INTERNAL_SHA256SUMS=PASS
AF8_CASE_COUNT=8
```

The route artifact's declared internal files all verify. The exact expected path set above is derived from `out/a-rest-svar-af8.tsv`; no path inference or coverage promotion occurred.

## Frozen source contract

The replacement workflow now:

- runs Python compile checks and the 12 strict decision-path regressions before Forge work;
- invokes `ws33_harden_a_rest_svar_af8_runtime.py` after the inherited harness transforms;
- invokes `ws33_adjudicate_a_rest_svar_af8.py` instead of the historical inline cleartext path verifier;
- requires positive target-effect evidence and real remote-client confidentiality sample evidence;
- requires production `PlaySpellAbility`, Forge cost/payment, Forge target/mode authority, source-root and target-AbilitySub reachability;
- compares decision/RNG/effect/client-sample/play-stage replay evidence;
- seals `SOURCE_CHAIN.json` and root `SHA256SUMS` in an `if: always()` step;
- uploads immutable evidence in an `if: always()` step;
- keeps `coverage_mutated=false` and `coverage_promotion=false`.

No commit after `SOURCE_HEAD` may be treated as part of run 34164631499. Parallel A-trigger/B-F preparation must occur on isolated branches and may not promote canonical coverage ahead of this verdict.
