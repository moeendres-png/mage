# WS33 ABC-A1 TargetRestrictions — terminal retry failure checkpoint

Date: 2026-09-05

## Exact transaction identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow source SHA: `0090e3ff693c1594b6a991dea65020ac69b04d22`
- workflow source tree: `8338c5b455d7b3475d7c871e2936021997421efe`
- run: `33937576612`
- job: `101228379574`
- terminal conclusion: `failure`

## Proven successful boundaries

The prior lineage defect is closed in this run:

- immutable model artifact `9823383539`: PASS
- artifact digest `sha256:aab73ba2ede151bbd0b803c2164d3067ddd65f17d49cf655c34eef67d903595d`: PASS
- authoritative manifest SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`: PASS
- consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`: PASS
- authoritative model count `4188`: PASS
- exact A1 queue binding `122` unique UNKNOWN IDs: PASS
- Forge pin: PASS
- WS01 / WS12 / WS32 retained prerequisite pins: PASS
- Decision / Hidden / RNG / WS33 / failure-semantics runtime overlay materialization: PASS

## Terminal failure boundary

`ws33_prepare_target_campaign.py` completed successfully and conservatively materialized `306` TargetRestrictions DECISION+REPLAY cases from the authoritative model.

The exact A1 filter then failed closed because five of the 122 queue-bound A1 paths were absent from the prepared campaign:

- `forge-behavior-v2:01655eb4cda1ef1a652a0c085ee7241a5ae241a7`
- `forge-behavior-v2:067bdc7754cc85e926900f11e4f1969088cf6da1`
- `forge-behavior-v2:09094286f77af4af8bafe7e1e1101a00c1ad0571`
- `forge-behavior-v2:0b34a03cf5d6174eb0eda60cd4f97abde7581ad7`
- `forge-behavior-v2:11dd247b928074ba858ba4d44aec905d2a69fb6a`

Record execution, tape-driven Replay and per-path certification were therefore skipped.

## Classification

- run facts: `DIRECTLY_VERIFIED`
- lineage repair: `DIRECTLY_VERIFIED`
- current failure class: `CAMPAIGN_MATERIALIZATION_GAP`
- exact root cause of the five omissions: `UNKNOWN` pending source/provenance adjudication
- Forge Rules Core defect: `NOT ESTABLISHED`
- behavior coverage produced by this run: `0`
- coverage promotion: `FALSE`

## Required next action

Inspect the authoritative manifest entries and exact pinned-Forge source/provenance for the five omitted paths. Repair only a systemic campaign-preparation/runtime-fixture gap if demonstrated. Do not add card-name/path-ID production hacks and do not relax cardinality or evidence gates.

## Frontier invariant

- TOTAL=4188
- PASS=366
- UNKNOWN=3822
- FAIL=0
- UNSUPPORTED=0
- ABC_UNKNOWN=1554
- WS33_COMPLETE=FALSE

`ABC_A1_RUN_33937576612=FAIL_CLOSED`
`ABC_A1_COVERAGE_PROMOTION=FALSE`
