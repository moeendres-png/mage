# WS33 G3 non-AF — Separate Certification Tooling Boundary

STATUS = DIAGNOSIS_CONFIRMED
TASK_COMPLETE = NO
WS33_COMPLETE = FALSE
COVERAGE_PROMOTION = FALSE
ACTIVE_PENDING_CHECKPOINT = NONE

## Live branch boundary before this checkpoint

- branch: `work/ws33-g3-final-closure-20260902`
- HEAD: `93b95c831d628fa2fdb564bc71f15026dc81c552`
- TREE: `8d31be1efab39278afc05e96ab40a7c46d99e771`

## Frozen non-AF runtime dependency

G3.1–G3.3 are frozen at:

```text
SOURCE_HEAD 2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7
SOURCE_TREE fbb9565d4583db655872cfd378831711b0989b7a
RUN         33928315020
JOB         101201530278
ARTIFACT    9957712911
DIGEST      sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b
```

The runtime artifact already directly proves 32/32 non-AF effective paths, 33/33 source parents, Decision-required 22/22, RNG-required 10/10, and tape-driven Record/Replay equality under the runtime workflow. It explicitly records `principal_observation_promoted=false` and `coverage_mutated=false`.

## Read-only tooling audit

The current branch contains:

- Direct-G ABI certification workflow: `.github/workflows/ws33-integrated-g-abi-request-evidence.yml` (fixed to 28 Direct-G paths);
- AF runtime certification / ABI replay workflows: `.github/workflows/ws33-g3-svar-af-runtime-v2-certify.yml` and `.github/workflows/ws33-g3-svar-af-abi-replay-v2.yml` (fixed to AF21 artifacts/cases);
- AF principal observation workflow: `.github/workflows/ws33-g3-svar-af-principal-observation-v5.yml`;
- generic adjudicator: `ws33_adjudicate_g_abi_request_evidence.py`;
- generic principal-observation adjudicators/instrumentation.

There is **no workflow for the non-AF/event 32-path separate ABI / Decision / RNG / Replay certification**, and no non-AF/event Principal Observation workflow.

Evidence classification: **DIRECTLY_VERIFIED** from the current branch workflow tree.

## Reusable generic adjudicator contract

`ws33_adjudicate_g_abi_request_evidence.py` is already generic across:

- Direct V15 case ABI;
- SVar AF V19 case ABI;
- SVar event V21 case ABI.

For V21 it explicitly permits duplicate parent rows only when the same effective path has identical requirement flags. It validates:

- exact expected unique path count;
- exact Decision-required and RNG-required path counts;
- byte-identical Record/Replay authoritative request traces;
- principal-scoped `(principal, token)` request identity;
- `PRINCIPAL_ONLY` visibility;
- opaque authoritative legal option IDs and uniqueness;
- request selection bounds;
- accepted Decision tape selections are members of the authoritative request option set and within min/max;
- every Decision-required path has accepted request/tape evidence;
- every RNG-required path has retained RNG evidence;
- no coverage mutation / no silent fallback in the emitted certification result.

The frozen non-AF artifact supplies the required V21 case file and Record/Replay request/Decision/RNG traces.

Evidence classification: **CODE_DERIVED** from current branch source.

## G3.4 implementation boundary

The smallest safe G3.4 successor is therefore a **qualification-only certification workflow**, not another Forge runtime execution and not another Rules repair.

It must:

1. download exact artifact `9957712911`;
2. verify GitHub digest and independent ZIP SHA256 `2241adad...aea0b`;
3. verify artifact `SHA256SUMS` and `diagnostic/SOURCE_CHAIN.json` exact pins/lineage;
4. invoke the existing generic adjudicator directly over the frozen artifact with `expected_paths=32`, `expected_decision_paths=22`, `expected_rng_paths=10`;
5. independently require the frozen artifact's Record/Replay semantic summaries, Decision/RNG tapes/events/requests to be byte-identical;
6. materialize an immutable certification chain referring to the exact runtime source HEAD/TREE/run/job/artifact/digest;
7. set `coverage_mutated=false` and never modify runtime evidence or coverage.

This does not invalidate G3.1–G3.3 because it consumes the immutable artifact read-only and introduces no Forge/runtime overlay change.

No Magic rules adjudication is required: this gate verifies Decision/RNG/replay ABI evidence already emitted by the Rules-resolved runtime; it does not infer legality.

## G3.5 boundary

Only after G3.4 terminal PASS, create/execute the separate non-AF Hidden31 Principal Observation successor using the existing principal-observation runtime contracts. It must preserve the exact runtime/model pins and prove principal-scoped Record/Replay visibility grant/use/revoke/no-leak semantics. Do not promote G before this gate passes.

## Next action

Create exactly one G3.4 certification workflow source commit targeting only its own workflow path, verify it creates exactly one intended run, persist PENDING identity immediately, and freeze writes until terminal adjudication.
