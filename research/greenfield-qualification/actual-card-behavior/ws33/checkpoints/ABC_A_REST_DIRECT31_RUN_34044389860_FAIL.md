# WS33 ABC A-rest Direct31 — run 34044389860 FAIL

Status: `FAIL`
Evidence classification: `DIRECTLY_VERIFIED` for run/artifact/compile failure; `CODE_DERIVED` for root-cause classification.

## Frozen run identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `.github/workflows/ws33-abc-a-rest-direct31-runtime.yml`
- source HEAD: `665f40e286b58912db27ba1734c0c9d92f52ae4b`
- source TREE: `06404df91656e8798a1e5cb3e9bdac853ca54e0d`
- run: `34044389860`
- job: `101516725121`
- run attempt: `1`
- conclusion: `failure`
- artifact: `9992681530`
- artifact name: `ws33-abc-a-rest-direct31-runtime-34044389860`
- artifact digest: `sha256:d9c224737a97f28602868d005df35c90fd8c88c37dbecc32424c010c445d4755`
- topology input artifact: `9980023181`
- topology input digest: `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`

## Independent artifact checks

The downloaded artifact ZIP independently hashes to exactly:

`d9c224737a97f28602868d005df35c90fd8c88c37dbecc32424c010c445d4755`

matching GitHub artifact metadata.

The embedded A-rest topology `SHA256SUMS` has 7 entries and all 7 verify. The artifact source-chain fragments report the expected frozen workflow HEAD/TREE above.

No `case-summary.tsv`, Decision tape, or replay result was produced. `record/` contains only `runtime.log` and `RNG_INVENTORY.json`.

## Terminal failure

Maven reached `forge-gui-desktop:testCompile` and failed before any qualification test ran:

```text
Ws33ARestDirectQualificationTest.java:[118,656] cannot find symbol
  symbol:   variable implementation
  location: variable c of type forge.net.Ws33ARestDirectQualificationTest.CaseSpec
```

Reactor result:

```text
forge-core        SUCCESS
forge-game        SUCCESS
forge-ai          SUCCESS
forge-gui         SUCCESS
forge-gui-desktop FAILURE
BUILD FAILURE
```

## Root cause

Classification: `HARNESS_ABI_COMPILE_DEFECT`.

The A-rest Direct31 adapter replaced historical `CaseSpec` with the 19-column A-rest ABI and removed the historical `implementation` field. A retained evidence-output path in the historical harness still references `c.implementation`, so the generated Java harness is internally inconsistent.

This failure occurred before actual-card witness execution. It does **not** establish a Forge Rules Core defect and cannot qualify or disqualify any A path semantically.

Repair scope is narrow and systemic: preserve/provide the implementation-target field expected by inherited evidence serialization, or update that serialization consistently with the new ABI. No card-name branch or rules-path change is required.

## Invariants

- `WITNESS_PATHS_EXECUTED=0`
- `COVERAGE_MUTATED=FALSE`
- `COVERAGE_PROMOTION=FALSE`
- `A_REST_UNKNOWN=57`
- `DIRECT31_RUNTIME_PASS=FALSE`

No repair may reuse this failed run as PASS evidence.
