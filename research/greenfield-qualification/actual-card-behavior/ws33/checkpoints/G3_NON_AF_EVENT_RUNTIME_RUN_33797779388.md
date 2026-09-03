# G3 NON-AF EVENT RUNTIME — RUN CHECKPOINT

Status: `RUNNING / UNADJUDICATED`

Evidence classification: `UNKNOWN` until the run and artifact are fully adjudicated.

## Workflow identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- workflow source HEAD: `0b1afc7be70f5a74b38516e3848f526f3693eac4`
- workflow source TREE: pending final run adjudication
- run: `33797779388`
- job: `100789526018`
- observed status at checkpoint creation: `in_progress`

## Scope

This run is the first focused non-AF Generation-3 event-parent runtime campaign after the immutable Direct-G 28-path and AF 21-path closures.

Expected frontier:

- effective paths: `32`
- source-proven parent entrypoints: `33`
- event-case ABI: `SVAR_EVENT_V21`
- direct target-SVar entry: `FALSE`
- trigger legality authority: Forge `TriggerHandler`
- Record/Replay required
- coverage mutation: forbidden
- principal-observation promotion: not part of this run

Pinned upstream topology:

- run: `33681121017`
- artifact: `9866293827`
- digest: `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`
- topology source HEAD: `4032d9c14dc7840e2518a92273037aaba443ada9`
- effective model SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`

Forge pin:

`8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Resume rule

Adjudicate run `33797779388` and job `100789526018` before any retry, replacement workflow, coverage promotion, or later G3 campaign. A green workflow alone is not a qualification PASS.
