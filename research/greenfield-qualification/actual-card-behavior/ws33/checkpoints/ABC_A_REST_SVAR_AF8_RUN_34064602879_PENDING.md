# WS33 ABC — A-rest SVar AF8 runtime — PENDING

Status: PENDING
Coverage promotion: FALSE

## Frozen source

- branch: `work/ws33-g3-final-closure-20260902`
- HEAD: `84fd0406906885e8c841dd06ef4230b3cc1cc3b4`
- TREE: `28e9269127f4242c9d8b25782618e91f7bab1510`
- workflow: `.github/workflows/ws33-abc-a-rest-svar-af8-runtime.yml`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Run

- RUN: `34064602879`
- JOB: `101571045115`
- expected artifact: `ws33-abc-a-rest-svar-af8-34064602879`

## Immutable route dependency

- route run: `34063748962`
- route artifact: `9998291348`
- route digest: `sha256:646594434eb987009561127f012bd0d974dcec97e67bef0bf478294f1fd9d0e9`
- route source HEAD: `48cb9a018f606f1209d14ee587a6ff3f14d263a1`
- route gate: 26 effective paths = AF8 + NestedTrigger1 + Trigger17, 27 runtime parent entrypoints, overlap 0, legality inference false.

## Qualification contract

This run may qualify exactly the 8 `ABILITY`-root A-rest SVar paths. It must prove, in fresh Record and fresh tape-driven Replay:

- exact 8-path identity set;
- actual-card source-parent binding;
- Forge `CharmEffect.makeChoices` where applicable;
- source-proven target mode selected only by membership in Forge-authoritative `MODE_SELECTION` options;
- Forge-authoritative minimum mode cardinality satisfied only from those authoritative options;
- generic public candidate fixtures only; no card/path-specific branch;
- Forge `SpellAbility.setupTargets`, MagicStack admission/resolution, and exact target-SVar resolution observation;
- required Decision evidence for all 8;
- zero path-scoped RNG for all 8;
- zero unauthorized/cross-principal hidden leakage;
- semantic Record/Replay equality;
- no direct resolve, no manual target injection, no standalone target-SVar entry;
- coverage mutation/promotion false.

`COVERAGE_PROMOTION=FALSE`
