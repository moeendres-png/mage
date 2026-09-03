# WS33 G3 AF ABI/replay v2 — PASS

Status: `PASS`

Evidence classification: `DIRECTLY_VERIFIED` for GitHub Actions, immutable artifact identity and retained record/replay outputs; `TECHNICALLY_CONFORMANT` for the strengthened AF request/RNG/replay ABI contract.

## Exact qualification identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `WS33 G3 SVar AF ABI replay v2`
- run: `33773805031`
- job: `100710378109`
- workflow source HEAD: `fe63c66a7be6215dffd4da85fc4cf7bf1de63b72`
- workflow source TREE: `6faa1a272201c5101fdf1533f8540ce99a4a3f8c`
- conclusion: `success`
- artifact id: `9901008043`
- artifact digest: `sha256:bf58a7154e8e2623bc9e6f4acf10c933b7d4fd692a357a643b881c586f4c15ef`

## Bound strengthened runtime baseline

- certified runtime-v2 source HEAD: `bd9998a30bd4f34603592aa06e7b16d2d3320047`
- certified runtime-v2 artifact id: `9900656730`
- certified runtime-v2 artifact digest: `sha256:b339b3eba6daaee5b7f59e9e3c05a7af611c1479ebd3d7b6e2c94d04f72e0708`
- strengthened witness source HEAD: `b3d02af402e55a65b11dcfec94def62be469a7a0`

## Gates proved

The Actions run completed every material gate successfully:

- exact certified runtime-v2 artifact and model identity verified;
- all pinned source HEAD/TREE values verified;
- exact runtime overlay stack applied;
- strengthened AF harness generated with no card-name/path-id branch;
- ABI adjudicator regression suite passed;
- fresh 21-path strengthened record passed with stack `1/1`, empty runtime failures, target-SVar reachability `>=1`;
- fresh record was byte-identical to the certified runtime-v2 baseline for case summary, decision tape/events, RNG tape/events and authoritative request trace;
- tape-driven strengthened replay passed;
- record/replay case summary, decision tape/events, RNG tape/events and request trace were byte-identical;
- all 12 replay-required paths reproduced exactly;
- strict authoritative request/RNG ABI adjudication passed for 21 paths, 9 decision-required paths and 4 RNG-required paths;
- authoritative legal options are retained only as opaque request options; request identity is principal-scoped; hidden identity payload retention is false; silent fallback is false;
- coverage mutation is false.

Additional real decision events on paths that are not source-marked `decision_required` remain admissible only because the ABI contract treats requirement flags as minima and still correlates every request/tape event against the authoritative request envelope. This includes the strengthened positive Scry witness.

## Serial consequence

This artifact supersedes historical AF ABI artifact `9890829899` for all strengthened AF Hidden / Principal Observation work. Principal-observation v5 must consume exactly artifact `9901008043` / digest `sha256:bf58a7154e8e2623bc9e6f4acf10c933b7d4fd692a357a643b881c586f4c15ef` and must apply the same source-dependent witness strengthener before principal-observation instrumentation.

AF runtime v2: `PASS`

AF ABI/replay v2: `PASS`

AF Hidden / Principal Observation: `UNKNOWN`

Coverage promotion: `FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
