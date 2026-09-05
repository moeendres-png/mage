# WS33 ABC-A1 TargetRestrictions — terminal failure checkpoint

Date: 2026-09-05

## Source / run identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow source SHA: `33cd3763f474ec66c9a94614b0813176c4e8665a`
- workflow source tree: `e868132d33c381bb569bdbf83aa50ac609a2aa39`
- run: `33936829551`
- job: `101226286827`
- terminal conclusion: `failure`

## Failure boundary

The run failed in `Verify exact source lineage and immutable model` before any Forge checkout, overlay materialization, campaign preparation, Record execution, Replay execution, or per-path certification.

The failing shell predicate was the hard equality check between the checked-in `WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json` SHA256 and the expected authoritative digest `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`.

## Classification

- workflow/run identity: `DIRECTLY_VERIFIED`
- failure boundary: `DIRECTLY_VERIFIED`
- root-cause class: `ORCHESTRATION_LINEAGE_GATE_DEFECT`
- Forge Rules Core defect: `NO EVIDENCE`
- Decision boundary defect: `NO EVIDENCE`
- behavior coverage produced: `0`
- coverage promotion: `FALSE`

## Required repair

Resolve the authoritative manifest lineage from immutable successor evidence and bind the campaign to that exact source. Do not weaken or delete the digest gate. Do not execute the runtime campaign until the exact model source is established.

## Frontier invariant

This failure does not change the post-G3 frontier:

- TOTAL=4188
- PASS=366
- UNKNOWN=3822
- FAIL=0
- UNSUPPORTED=0
- ABC_UNKNOWN=1554
- WS33_COMPLETE=FALSE

`ABC_A1_RUN_33936829551=FAIL_CLOSED`
`ABC_A1_COVERAGE_PROMOTION=FALSE`
