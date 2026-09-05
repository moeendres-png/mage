# G3 AF PRINCIPAL OBSERVATION V5 — INCIDENTAL REQUALIFICATION RUN 33929441412 PASS

This run was an unintended second workflow trigger from source commit `a7e1d6b2863ba78ee738f25b6d33317cf05e5e94`, caused by the shared principal-observation tooling path. The run-cardinality incident was persisted before terminal execution. No third run was created from that source commit.

Evidence classification: `DIRECTLY_VERIFIED` for run/job/step/artifact metadata.

## Identity

- source HEAD: `a7e1d6b2863ba78ee738f25b6d33317cf05e5e94`
- source TREE: `0c2695708994264fa1e6556bac5ead59ad521fad`
- workflow: `.github/workflows/ws33-g3-svar-af-principal-observation-v5.yml`
- run: `33929441412`
- job: `101204860983`
- conclusion: `success`

## Terminal gates

All AF v5 steps passed, including exact ancestry/pins, immutable AF ABI v2 consumption, runtime artifact availability, dependency pins, principal-scoped observation runtime stack, strengthened harness, v5 classifier regressions, fresh Record, tape-driven Replay, observation-only nonperturbation, strict shape-aware adjudication, source-chain hashes, and artifact upload.

Terminal adjudication output:

`WS33_G_PRINCIPAL_OBSERVATION=PASS paths=21 hidden=19 record_events=24 replay_events=24 retained_hidden_ids=0 cross_principal_leaks=0`

Nonperturbation output:

`WS33_G_SVAR_AF_V5_OBSERVATION_ONLY=PASS paths=21 parents=21 decision_tape_equal=true rng_tape_equal=true semantic_digests_equal=true`

## Artifact

- artifact ID: `9958136895`
- name: `ws33-g3-svar-af-principal-observation-v5-33929441412`
- GitHub digest: `sha256:deef7497dd5f4d9837b1c747462f0bfef30d8f0080174a0a8a814cfd12b75022`
- artifact size: `102935` bytes

This PASS strengthens, rather than invalidates, the already-qualified AF21 evidence. No global coverage promotion is performed here.
