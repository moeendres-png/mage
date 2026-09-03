# G3 NON-AF EVENT RUNTIME — CORRECTIVE RUN CHECKPOINT

Status: `QUEUED/RUNNING / UNADJUDICATED`

Evidence classification: `UNKNOWN` until the run and its immutable artifact are fully adjudicated.

## Run identity

- workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- source HEAD: `935da1abf48b84f85e4265a26ba65fb546e8cb07`
- source TREE: `f2ede3993608c0a7bf92461462124112d57dcf21`
- run: `33798342466`
- job: `100791376533`
- observed state when checkpointed: `queued`

## Repair embodied by source HEAD

This corrective source changes only the adjudicated pre-runtime infrastructure defects from run `33797779388`:

- topology consumer-model SHA256 is bound separately as `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`;
- predecessor effective-manifest file SHA256 remains separately retained as `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`;
- current qualification tooling checkout uses `fetch-depth: 1`;
- early failure evidence uploads the existing `generated/` tree instead of requiring a late-created hash manifest.

No non-AF behavior or coverage has been promoted by this commit.

## Resume rule

Adjudicate run `33798342466` / job `100791376533` before any additional retry or workflow repair. If the run fails, persist the first material root cause and artifact identity/digest before changing code. If it passes, independently verify the uploaded artifact and machine/source-chain evidence before classifying Runtime Record/Replay PASS.
