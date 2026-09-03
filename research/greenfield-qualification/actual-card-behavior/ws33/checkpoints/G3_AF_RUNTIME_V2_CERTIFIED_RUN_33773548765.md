# WS33 G3 AF runtime v2 — certified PASS

Status: `PASS`

Evidence classification: `DIRECTLY_VERIFIED` for GitHub Actions, immutable artifact identity, and retained runtime outputs; `TECHNICALLY_CONFORMANT` for the strengthened 21-path AF runtime witness contract.

## Exact certification identity

- branch: `work/ws33-g3-final-closure-20260902`
- certification workflow: `WS33 G3 SVar AF runtime v2 certification`
- certification run: `33773548765`
- certification job: `100709510471`
- certification HEAD: `bd9998a30bd4f34603592aa06e7b16d2d3320047`
- certification TREE: `15fd647dc3ed5034176a2388c5540eaeadc9f9c5`
- conclusion: `success`
- certified artifact id: `9900656730`
- certified artifact digest: `sha256:b339b3eba6daaee5b7f59e9e3c05a7af611c1479ebd3d7b6e2c94d04f72e0708`

## Bound source runtime evidence

The certification consumes exactly:

- source runtime run: `33769086465`
- source job: `100694379650`
- source HEAD: `7fc18ccd062278d8690e77c0b04fad44bc9b213b`
- source TREE: `992da510930c5e0c9b919feb3e4319655e1f6aec`
- source artifact id: `9899227922`
- source artifact digest: `sha256:ee3de852a4eedf3e96638a2c48ce8d549da9471d49b4b49df51259d3ca5bfb2e`

## Certified runtime contract

The certification revalidated the immutable source artifact fail closed and proved:

- exactly 21 AF cases, 19-column source ABI;
- every runtime summary row is `PASS`;
- runtime failure type/message are empty;
- stack admission/resolution are `1/1` for every path;
- target-SVar reachability is `>=1` for every path;
- strengthened witness transform is `PASS`;
- card-name branching = `0`;
- path-id branching = `0`;
- the unique source-dependent `ScryNum$ X` target reaches an authoritative positive Scry branch;
- that path records both `TARGET_SELECTION` and `SCRY_BOTTOM_SELECTION` in decision events and request evidence;
- decision event count for that path is at least `2`;
- coverage mutation is `FALSE`.

The earlier runtime-v2 workflow failure is therefore adjudicated as a superseded post-runtime gate-name defect (`INPUT_CONFIRM` vs actual `SCRY_BOTTOM_SELECTION`), not a Forge runtime failure.

## Serial consequence

This certified artifact is now the only eligible AF runtime-v2 baseline for the next ABI/replay qualification. The historical behavior artifact `9889684290` must not be used as the runtime baseline for the strengthened Scry witness.

AF behavior runtime v2: `PASS`

AF ABI/replay v2: `UNKNOWN`

AF Hidden / Principal Observation: `UNKNOWN`

Coverage promotion: `FALSE`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
