# WS33 G3 AF Principal Observation v4 — corrective run checkpoint

Status: `PARTIAL`

Evidence classification: `DIRECTLY_VERIFIED` for source/run/job identity. Qualification remains `UNKNOWN` until completion and artifact adjudication.

## Current work package

Re-run the focused AF Principal Observation / Hidden Information gate only after fixing the diagnosed overlay source-split defect from run `33755201667` and the pre-acceptance evidence-hash self-inclusion defect.

## Corrective changes bound to this run

- workflow now applies the current G3 successor `apply-ws33-input-confirm.py`, which contains the Principal Observation base infrastructure, before the current fail-closed observation-fanout and external-card-decision-lifetime overlays;
- immutable Direct-G Behavior source remains the source for retained WS05/WS06/stack-target runtime pieces;
- immutable AF Behavior source remains the source for target-selection/SVar reachability pieces;
- no `replace_once` anchor was loosened;
- Direct-G attribution compatibility remains a static/instrumentation proof in this gate, not a redundant Direct-G qualification rerun;
- `EVIDENCE_SHA256SUMS.txt` is now generated via a temporary path and explicitly excluded from its own input set.

## Source identity

- repository: `moeendres-png/mage`
- branch: `work/ws33-g3-final-closure-20260902`
- workflow source HEAD: `104f40216cf161363f2e2178c1bcbf27368c518d`
- workflow source TREE: `52d102c95a1b71dd7a869b248872e95ae25dbc39`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective model SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`

## Run

- run: `33756098495`
- job: `100650763479`
- workflow: `WS33 G3 SVar AF principal observation v4`
- status at checkpoint: `in_progress`
- conclusion: `UNKNOWN`
- artifact: `UNKNOWN` until upload completes
- artifact digest: `UNKNOWN` until upload completes

## Predecessor evidence retained

AF Behavior:
- HEAD `28f4e7cdd6a35c488d4633cf8d77163a8aa2d5d9`
- TREE `fa5cb7385b2724433cf877b11e890985adef2376`
- artifact `9889684290`
- digest `sha256:7a9b8a4e8dd993d419d55fa31763ef8d49ffc3927408bfdb4488724dd16d68e9`

AF ABI/Decision/RNG/Replay:
- HEAD `b599cb1550c3e04f099eb59dd4aae1e117078167`
- TREE `9944a7f8295222839f4efef92be562c84ebc09ef`
- run `33748782606`
- job `100627296583`
- artifact `9890829899`
- digest `sha256:77fe10f72233e824169829a2e7526103cb0bacf8b06823379ce57f44472359eb`

## Required result

- paths `21`
- hidden required `19`
- Record coverage `21/21`
- Replay coverage `21/21`
- target-SVar reachability retained `21/21`
- principal transport `REMOTE_CLIENT_DELTA`
- retained hidden identity payload `false`
- unauthorized/private leak delta `0`
- cross-principal leak delta `0`
- required positive lifecycle complete per `(principal,card)`
- unknown hidden consumer profile fails closed
- deterministic Record/Replay observation evidence
- behavior/Decision/RNG traces nonperturbed except the historical coarse hidden-leak summary field being superseded by principal-scoped evidence
- coverage mutated `false`

## Known open semantic point

One hidden-required AF target consumer is `Manifest`. It is intentionally not pre-waived or guessed by the classifier. If the gate reaches adjudication and reports an unknown Manifest hidden-consumer profile, that failure is the next semantic work package and must be resolved against the actual Forge visibility lifecycle and current official rules before any AF promotion.

## Exact next step

Adjudicate run `33756098495` / job `100650763479` to the first material failure or completion. If successful, verify artifact/digest/downloaded ZIP and machine evidence before creating an immutable PASS checkpoint.

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
