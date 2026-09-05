# G3 NON-AF PRINCIPAL OBSERVATION — RUN 33929441452 PASS

Evidence classification: `DIRECTLY_VERIFIED` for GitHub run/job/step/artifact metadata; retained workflow conclusions are accepted only where the terminal workflow gate itself passed.

## Source / run identity

- branch: `work/ws33-g3-final-closure-20260902`
- source HEAD: `a7e1d6b2863ba78ee738f25b6d33317cf05e5e94`
- source TREE: `0c2695708994264fa1e6556bac5ead59ad521fad`
- workflow: `.github/workflows/ws33-g3-svar-event-principal-observation.yml`
- run: `33929441452`
- job: `101204861149`
- conclusion: `success`

## Frozen prerequisite bindings

- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- non-AF runtime run: `33928315020`
- runtime artifact: `9957712911`
- runtime digest: `sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b`
- G3.4 certification run: `33928888207`
- G3.4 certification artifact: `9957891877`
- G3.4 certification digest: `sha256:2a5a2a9a56a640f5a52fd57f681c8f0719c4f02b83a7db2c9cdd1a22d2c93a21`
- topology consumer-model SHA256: `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`
- effective-manifest file SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`

## Terminal gates

All intended G3.5 steps completed successfully, including:

- exact frozen prerequisite binding;
- runtime + observation overlays;
- source-parent event harness with principal-observation attribution;
- fresh principal-observation Record;
- tape-driven principal-observation Replay;
- Hidden31 principal-observation adjudication;
- immutable observation-chain materialization;
- artifact upload.

Workflow adjudication output:

`WS33_G_PRINCIPAL_OBSERVATION=PASS paths=32 hidden=31 record_events=88 replay_events=88 retained_hidden_ids=0 cross_principal_leaks=0`

The generated chain reports `hidden_required_paths=31`, `record_replay_equal=true`, `retained_hidden_identity_payload=false`, `cross_principal_leaks=0`, `coverage_mutated=false`, `rules_mutation=false`, `pilot_fallback=false`.

## Artifact

- artifact ID: `9958147261`
- name: `ws33-g3-svar-event-principal-observation-33929441452`
- GitHub digest: `sha256:5d7ab4034b3b674b3d907a50dfb3d7f5bbac5a3eb1abaf8c0ec42eeb1c958ed5`
- artifact size: `144756` bytes

The workflow itself materialized `SHA256SUMS` before upload. No coverage promotion is performed in this checkpoint.

## Adjudication

`G3.5 PRINCIPAL OBSERVATION = PASS`

`NON_AF32_RUNTIME = PASS`

`NON_AF32_ABI_DECISION_RNG_REPLAY_CERT = PASS`

`NON_AF32_HIDDEN31 = PASS`

G3-wide promotion remains a separate G3.6 cross-qualification step; this file does not independently set global coverage.
