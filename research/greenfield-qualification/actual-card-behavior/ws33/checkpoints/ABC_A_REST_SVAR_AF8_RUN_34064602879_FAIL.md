# WS33 ABC — A-rest SVar AF8 — Run 34064602879 — TERMINAL FAIL

Status: `FAIL`
Evidence classification: `DIRECTLY_VERIFIED` for GitHub Actions terminal/run/artifact metadata; detailed semantic root cause remains `UNKNOWN` pending exact adjudicator diagnosis.

## Frozen run identity

- Branch: `work/ws33-g3-final-closure-20260902`
- SOURCE_HEAD: `84fd0406906885e8c841dd06ef4230b3cc1cc3b4`
- SOURCE_TREE: `28e9269127f4242c9d8b25782618e91f7bab1510`
- RUN: `34064602879`
- JOB: `101571045115`
- Workflow conclusion: `failure`

## Step adjudication

- Record AF8 runtime: `SUCCESS`
- Replay AF8 runtime: `SUCCESS`
- Adjudicate AF8 rung (fail closed): `FAILURE`
- Upload immutable AF8 evidence: `SUCCESS`

The workflow failure therefore occurs in fail-closed adjudication after both runtime executions completed. This checkpoint does not infer which adjudication invariant failed.

## Immutable artifact metadata

- ARTIFACT_ID: `9998600937`
- ARTIFACT_NAME: `ws33-abc-a-rest-svar-af8-34064602879`
- ARTIFACT_SIZE_BYTES: `538169679`
- ARTIFACT_DIGEST: `sha256:2cf9c070ef04249eece466ce0b627b7e2c7a9270b57b54c923a1a5472361f3ec`

The previously carried artifact reference `10006835993` is stale for this run and MUST NOT be used as the canonical run artifact.

## Promotion boundary

- `COVERAGE_PROMOTION=FALSE`
- Witness/adjudication failure MUST NOT mutate global WS33 coverage.
- Coverage remains: `TOTAL=4188 PASS=488 UNKNOWN=3700 FAIL=0 UNSUPPORTED=0`.
- Bucket A remains `57 UNKNOWN`.
- `WS33_COMPLETE=FALSE`.
- `PROJECT=INCOMPLETE`.
- `ARCHITECTURE_FREEZE=NOT_ADJUDICATED`.

## Resume gate

Before any AF8 source repair or replacement run:

1. obtain the exact failed adjudicator diagnostic from run/job evidence and/or immutable artifact evidence;
2. classify the root cause without guessing;
3. persist a separate `ROOT_CAUSE` checkpoint;
4. only then make the minimal systemic repair and register a fresh frozen Record+Replay run.
