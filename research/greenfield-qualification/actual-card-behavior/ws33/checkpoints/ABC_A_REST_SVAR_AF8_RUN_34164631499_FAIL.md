# AF8 replacement run 34164631499 — terminal FAIL

```makefile
STATUS=FAIL
COVERAGE_MUTATED=FALSE
COVERAGE_PROMOTION=FALSE

RUN=34164631499
JOB=101873135926
SOURCE_HEAD=895240f4058076764227a418ad28e84f61d3a7ed
SOURCE_TREE=cec73ae51b0168280ea648892f3e9edd46dcd883
WORKFLOW=.github/workflows/ws33-abc-a-rest-svar-af8-runtime.yml
FORGE_PIN=8c7e9afb8e6caee88644b94e25da5852e36f8928
EXPECTED_PATH_COUNT=8
EXPECTED_PATH_SET_SHA256=10c3825fa3ba1e58aadcaacad1012263c4201438cf8c694db6cb10b3bae7b0f1

ARTIFACT=10033797771
ARTIFACT_NAME=ws33-abc-a-rest-svar-af8-34164631499
ARTIFACT_SIZE_BYTES=538388200
ARTIFACT_METADATA_DIGEST=sha256:a91c512759d37c47ae6ee3f3b07f156ea9dcb0f11301a8d1272035e970a174f4
FAILED_STEP=Fresh AF8 Record
SEAL_STEP=SUCCESS
UPLOAD_STEP=SUCCESS
```

## Exact failure

DIRECTLY_VERIFIED from job 101873135926 logs:

`forge-gui-desktop:testCompile` fails before the AF8 JUnit test can execute. The generated harness references two observation-only qualification APIs that are absent from the overlaid pinned-Forge source used by this workflow:

1. `forge.game.zone.MagicStack.setWs33ResolutionObserver(...)`
2. `forge.game.player.PlaySpellAbility.setWs33PlayStageObserver(...)`

Four compiler errors are emitted: observer installation and cleanup for both APIs. Reactor modules through `forge-gui` succeed; `forge-gui-desktop` fails at test compilation. Therefore Record does not execute, Replay/adjudication are skipped, and no behavior PASS is possible.

## Root-cause classification

```makefile
ROOT_CAUSE=QUALIFICATION_OVERLAY_DEPENDENCY_OMISSION
ENGINE_SEMANTIC_DEFECT=NOT_DEMONSTRATED
CARD_BEHAVIOR_FAILURE=FALSE
PATH_ROUTE_PROJECTION=NOT_THIS_FAILURE
```

The AF8 hardener correctly inserted source-root and play-stage observation calls, but the workflow applied only the pre-existing stack-target/target-selection/SVar overlays. It did not apply the companion observer overlays (or equivalent generic observer additions) needed to make the hardener-generated harness compile. This is a qualification integration defect, not evidence of incorrect Magic behavior in pinned Forge.

## Failure-resilient artifact result

The workflow repair itself worked as intended:

- `Seal AF8 evidence even on failure` completed successfully.
- root `SOURCE_CHAIN.json` and `SHA256SUMS` were generated.
- the seal step verified every file listed by root `SHA256SUMS`.
- artifact upload completed successfully despite Record failure.
- GitHub artifact metadata and upload log agree on digest `sha256:a91c512759d37c47ae6ee3f3b07f156ea9dcb0f11301a8d1272035e970a174f4` and size 538388200 bytes.

The artifact is larger than the current connector download ceiling, so independent outer-ZIP download verification is not yet claimed from this chat. The server-side metadata digest is DIRECTLY_VERIFIED; internal manifest verification is DIRECTLY_VERIFIED from the always-run sealing logs.

## Repair scope

Repair only the invalidated AF8 integration gate:

1. identify the existing generic observation overlay(s), if already persisted, that add the two APIs;
2. if absent, add generic observation-only overlays for `MagicStack` source-root resolution and `PlaySpellAbility` play stages, without legality/rules mutation;
3. apply them before AF8 test compilation;
4. add cheap source/static checks that the two APIs exist before Maven;
5. rerun parser/static validation;
6. freeze a new source HEAD/TREE and run a replacement AF8 Record/Replay qualification;
7. do not modify canonical coverage unless a later immutable PASS is independently adjudicated.

Historical run 34064602879 remains separately preserved for `PATH_ROUTE_PROJECTION`; this run is a distinct compile-time integration failure and does not supersede that historical evidence.
