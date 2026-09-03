# WS33 G3 AF Principal Observation v4 — run checkpoint

Status: `PARTIAL`

Evidence classification: `DIRECTLY_VERIFIED` for GitHub run/job/source identity. Qualification result is `UNKNOWN` until the run completes and the artifact is adjudicated.

## Current work package

Qualify Principal Observation / Hidden Information for the 21 source-proven AbilityFactory-compatible G SVar paths, of which 19 require hidden-information evidence, using the existing Direct-G principal-observation transport and a target-consumer-aware AF case ABI.

## Target state

- effective paths `21`
- hidden-required paths `19`
- record campaign coverage `21/21`
- replay campaign coverage `21/21`
- principal transport `REMOTE_CLIENT_DELTA`
- retained hidden identity payload `false`
- unauthorized/private leak delta `0`
- cross-principal leak delta `0`
- positive temporary hidden lifecycle per `(principal,card)`: `SERVER_GRANT -> CLIENT_VISIBLE -> SERVER_REVOKE -> CLIENT_HIDDEN`
- unknown hidden consumer profile: fail closed
- deterministic Record/Replay observation evidence
- no coverage mutation

## Source identity

- repository: `moeendres-png/mage`
- branch: `work/ws33-g3-final-closure-20260902`
- workflow source HEAD: `52794dcf29c7d673630ad7d96e91f596af57aec9`
- workflow source TREE: `28597fcdcebfd4dde6ecbfe7e7c8bbc108a9e26d`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective model SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`

## Reused immutable predecessor evidence

AF Behavior:
- source HEAD `28f4e7cdd6a35c488d4633cf8d77163a8aa2d5d9`
- source TREE `fa5cb7385b2724433cf877b11e890985adef2376`
- artifact `9889684290`
- digest `sha256:7a9b8a4e8dd993d419d55fa31763ef8d49ffc3927408bfdb4488724dd16d68e9`

AF ABI / Decision / RNG / Replay:
- source HEAD `b599cb1550c3e04f099eb59dd4aae1e117078167`
- source TREE `9944a7f8295222839f4efef92be562c84ebc09ef`
- run `33748782606`
- job `100627296583`
- artifact `9890829899`
- digest `sha256:77fe10f72233e824169829a2e7526103cb0bacf8b06823379ce57f44472359eb`

## Implemented in this package

- Base principal-observation adjudicator now accepts `--expected-paths`, defaulting to Direct-G-compatible `28`.
- Exact case ABI discrimination: Direct-G v15 or AF v19 only; unknown/mixed ABI fails closed.
- AF hidden-profile classification uses the actually executed target consumer: `targetDispatch=f[17]`, `targetScript=base64(f[18])`; it does not classify from the source-parent dispatch/script.
- Campaign execution coverage is distinct from optional/negative observation-event cardinality.
- Observation instrumenter accepts exactly one Direct-G or AF attribution anchor and fails closed for missing/duplicate/mixed anchors.
- AF anchor: `currentPath.set(spec.pathId);prepareSourceParentChoices(spec,sa);bindTargets(sa);`.
- No legality, target, decision, RNG, or stack-choice inference was added.
- Focused workflow: `.github/workflows/ws33-g3-svar-af-principal-observation-v4.yml`.
- Workflow consumes the immutable AF ABI artifact and exact AF Behavior identity, proves Direct-G anchor compatibility without rerunning Direct-G qualification, executes fresh AF Record/Replay, checks target-SVar reachability, and adjudicates strict principal-scoped lifecycle/leak invariants.

## Current run

- run `33755201667`
- job `100647860029`
- workflow: `WS33 G3 SVar AF principal observation v4`
- status at checkpoint: `in_progress`
- conclusion: `UNKNOWN`
- artifact: `UNKNOWN` until upload completes
- artifact digest: `UNKNOWN` until upload completes

## Known failures

None adjudicated yet for this run. A green workflow is not accepted as qualification evidence until job steps, artifact contents, source identity and digest are checked.

## Open points

1. Adjudicate run `33755201667` to completion.
2. If failed, identify the first material failure and repair systemically; do not blind rerun.
3. If green, verify artifact identity/digest, download/hash the immutable ZIP, inspect `WS33_G_AF_PRINCIPAL_OBSERVATION.json` and `SOURCE_CHAIN.json`, and persist the immutable PASS checkpoint.
4. Only after that decide AF promotion eligibility; no AF coverage promotion has occurred at this checkpoint.

## Exact next step

Fetch run/job state for `33755201667` / `100647860029`; when complete, adjudicate the first non-green step or the uploaded artifact.

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
