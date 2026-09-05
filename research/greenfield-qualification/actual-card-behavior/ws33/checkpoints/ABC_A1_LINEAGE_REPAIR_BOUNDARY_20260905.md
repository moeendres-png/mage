# WS33 ABC-A1 — authoritative model lineage repair boundary

Date: 2026-09-05

## Directly verified lineage

The failed run `33936829551` incorrectly compared the checked-in branch manifest to the authoritative Generation-2/Generation-3 model digest.

The successful G3 consumer-topology workflow at source `4032d9c14dc7840e2518a92273037aaba443ada9` proves the actual lineage:

- authoritative model artifact ID: `9823383539`
- authoritative model artifact ZIP digest: `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`
- authoritative `WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json` SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- authoritative effective path count: `4188`
- authoritative coverage in that model artifact: `PASS=285`, `UNKNOWN=3903`
- consumer model SHA256: `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`

The artifact was independently downloaded and its ZIP SHA256 and manifest SHA256 matched the values above.

## Repair contract

The ABC-A1 workflow must:

1. download artifact `9823383539` itself;
2. verify the immutable artifact digest;
3. verify the manifest digest;
4. use that artifact manifest as the campaign source, not the stale checked-in manifest;
5. bind the 122 queue IDs to that exact manifest and verify each is present and `UNKNOWN` in the artifact coverage;
6. keep the queue scope exact: `WS33A / TargetRestrictions / ws33-g2-template-123 / DECISION+REPLAY`;
7. fail closed on any cardinality, lineage, runtime, Record, Replay, Decision, or evidence mismatch;
8. perform no coverage mutation in the campaign run.

No digest gate is weakened or removed.

`ABC_A1_LINEAGE_ROOT_CAUSE=RESOLVED`
`ABC_A1_RETRY_ELIGIBLE=TRUE`
`COVERAGE_PROMOTION=FALSE`
