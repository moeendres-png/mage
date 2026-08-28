# Targeted Requalification — `34036a2d`

Date: 2026-08-28

The strict decision patch changed at this revision. Only affected evidence was
rerun; unchanged requirement, licensing, matrix, and external-reference
artifacts were not duplicated.

| Affected boundary | Exact run / artifact | Artifact SHA-256 | Result |
|---|---:|---|---|
| Typed decision boundary | `33152614647` / `9678342430` | `1cf3fb821bae89ebc4761c412a7609862179698c1de2d862ad2219c9d49fbe67` | Static contract, 24 negative-path tests, patch application, and compile pass; Q1 remains `FAIL` |
| Raw hidden transport | `33152614611` / `9678348191` | `126f4062334510582b7fc9eaace074e3568b3805397334a1d8fc88f0d1ca23c8` | Scoped 2P decoded transport `PASS`, leak count `0` |
| Decision/RNG census | `33152614624` / `9678318483` | `bf9be7008c4f14764ec04c624d5451d7147b61296fe7f27a02f863ed7b630f2f` | `FAIL`: 109 controller callbacks, 15 blocking GUI paths, 10 fallback findings, 8 direct RNG bypasses |
| Runtime / replay | `33152614679` / `9678412031` | `6798a2841e45e8b9aada2411d1739280dba507ad769d075a84598cf3e189a8de` | 2P–5P and RogShai CLI probes pass; semantic replay remains `NOT_RUN` due to missing state/RNG/Decision tapes |

All four runs bind to source head
`34036a2d6704c0b70c0a59d071bc938870db0c2b`, tree
`33e3968b35fc5cd2967f12d8f57c4b7ebab2d21f`, Forge pin
`8c7e9afb8e6caee88644b94e25da5852e36f8928`, and strict patch SHA-256
`42ff6d7301287af90b3c5b1ba9d809d78f19018d80f4a8ba5b0eeacad0d1e581`.

This is a provenance-scoped evidence transfer, not a production acceptance.
The first blocking gate remains
`FULL_DECISION_CENSUS_NOT_EXTERNALIZED`; architecture freeze stays `FALSE`.
