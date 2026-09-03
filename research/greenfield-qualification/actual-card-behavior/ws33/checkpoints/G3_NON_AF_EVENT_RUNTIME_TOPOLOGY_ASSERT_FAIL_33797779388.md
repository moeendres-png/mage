# G3 NON-AF EVENT RUNTIME — TOPOLOGY ASSERT FAILURE

Status: `ADJUDICATED FAILURE / NO RUNTIME EXECUTION`

Evidence classification: `UNKNOWN` for the 32 non-AF effective paths. This run is a pre-runtime qualification-infrastructure failure and is not evidence of an engine/card-behavior failure.

## Immutable run identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- source HEAD: `0b1afc7be70f5a74b38516e3848f526f3693eac4`
- source TREE: `e9d39da970809555e3246cb2b156ac7156cc3ae5`
- run: `33797779388`
- job: `100789526018`
- job conclusion: `failure`
- artifacts: `NONE`

## First material failure

Step 3, `Consume exact immutable topology and materialize event cases`, failed before any Forge checkout, overlay application, Java build, Maven test, Record campaign, or Replay campaign.

The workflow asserted:

```text
.status == PASS
.remaining_svar_count == 53
.effective_model_sha256 == cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224
```

The exact immutable topology artifact instead contains:

```text
schema = commander-simulator-next.ws33-g-svar-consumer-topology.v2
status = PASS
remaining_svar_count = 53
effective_model_sha256 = 82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48
```

The topology generator at source HEAD `4032d9c14dc7840e2518a92273037aaba443ada9` defines that field as `man['consumer_model_sha256']`. Therefore the workflow incorrectly compared a consumer-model hash field with the earlier Effective-Manifest file SHA256 `cd48f427...`. These are distinct hash semantics.

Pinned topology provenance that did pass before the failing assertion:

- topology run: `33681121017`
- topology source HEAD: `4032d9c14dc7840e2518a92273037aaba443ada9`
- topology artifact: `9866293827`
- topology artifact digest: `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`
- artifact schema/status/count: `v2 / PASS / 53`

## Secondary failure

The `if: always()` upload step also failed because its path set included `generated/SHA256SUMS`, which had not yet been created after the early Step-3 abort. No artifact was emitted for this failed run.

This secondary upload failure does not change the first material root cause.

## Qualification effect

- non-AF effective paths remain: `32 UNKNOWN`
- source-proven parent entrypoints remain: `33 UNQUALIFIED`
- coverage promotion: `FALSE`
- principal-observation promotion: `FALSE`
- runtime behavior failure: `NOT ESTABLISHED`
- retry permitted only after a persisted workflow repair

## Required repair

1. Preserve both hash semantics explicitly instead of equating them:
   - effective manifest file SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
   - topology consumer-model SHA256: `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`
2. Bind the topology assertion to the exact consumer-model hash from the immutable topology evidence.
3. Make partial-failure artifact upload robust by uploading the existing `generated/` tree rather than requiring a late-created hash file.
4. Reduce the current-tooling checkout to `fetch-depth: 1`; full history is not consumed by this workflow.
5. Persist the repair commit before the next run, then checkpoint and adjudicate exactly that corrective run before any further retry.
