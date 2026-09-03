# WS33 G3 AF Principal Observation v4 — overlay composition failure

Status: `FAILED` for this gate attempt; AF Principal Observation qualification remains `OPEN` / `UNKNOWN` because no runtime qualification execution occurred.

Evidence classification: `DIRECTLY_VERIFIED` for GitHub source/run/job/artifact identity and step outcome; `CODE_DERIVED` for the root-cause diagnosis below.

## Current work package

Qualify Principal Observation / Hidden Information for the 21 AbilityFactory-compatible G SVar paths (19 hidden-required) without rerunning already immutable AF Behavior/Decision/RNG/Replay evidence.

## Run identity

- repository: `moeendres-png/mage`
- branch: `work/ws33-g3-final-closure-20260902`
- workflow: `WS33 G3 SVar AF principal observation v4`
- workflow source HEAD: `52794dcf29c7d673630ad7d96e91f596af57aec9`
- workflow source TREE: `28597fcdcebfd4dde6ecbfe7e7c8bbc108a9e26d`
- run: `33755201667`
- job: `100647860029`
- run status/conclusion: `completed/failure`
- artifact: `9893240608`
- artifact digest: `sha256:15203c5cab425e46c06b2142231a8f29de7f2a02b73af1442f39501fd0cd81b4`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective model SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`

## Step adjudication

Freshly verified PASS before the first material failure:

1. checkout current G3 successor tooling;
2. exact serial ancestry / source trees;
3. immutable AF ABI artifact identity and digest;
4. immutable AF Behavior artifact identity;
5. exact checkouts for Direct-G source, AF Behavior source, Forge, WS01, WS12, WS32 and historical WS31 harness;
6. exact source-pin verification.

First material failure:

`Apply green AF runtime plus Direct-G principal-observation transport`

The overlay log terminates with:

`WS33_OBSERVATION_FANOUT=FAIL public reveal host exception: expected anchor once, found 0`

All runtime execution, Record/Replay, principal-observation adjudication and final evidence materialization steps were correctly skipped. Therefore this run does **not** prove an AF behavior/rules failure and does **not** alter any qualification coverage.

## Root cause

The failure is an overlay-source composition error introduced by the new AF Principal Observation workflow, not a production-rules failure.

The immutable Direct-G Principal Observation v4 PASS run `33552816460` executed source HEAD `3be666cc268456274204d39b2bd3c208f0d8c41e`. At that source, the WS33 `apply-ws33-input-confirm.py` overlay contains the principal-observation base infrastructure (`ExternalObservationTrace` and `beginWs33ExternalCardObservation(...)`) that `apply-ws33-observation-fanout.py` intentionally hardens.

The failed AF workflow instead applied `direct-source/$ROOT/runtime-overlays/apply-ws33-input-confirm.py` from immutable Direct-G Behavior source `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`. That older/split input-confirm overlay contains transport/reveal externalization but **not** the later principal-observation base anchor. The current observation-fanout overlay therefore correctly failed closed rather than silently applying an incomplete observation contract.

The exact AF ABI/Behavior runtime split remains valid for its already-qualified Behavior/Decision/RNG/Replay obligations. Principal Observation adds a later, separately qualified observation-only overlay layer and must use the current principal-observation base overlay, whose Direct-G v4 compatibility is independently preserved by the workflow.

## Additional pre-retry defect found by review

The new workflow's planned `EVIDENCE_SHA256SUMS.txt` command includes the output file itself in the `find ... diagnostic ...` input set because shell redirection creates the file before `find` runs. This attempt never reached that step, so no evidence was accepted. Before retry, the hash materializer must exclude the destination or write to a temporary path outside the enumerated set and move it afterward.

## Decisions

- no blind rerun of `33755201667`;
- do not weaken `replace_once` or allow missing observation anchors;
- preserve exact AF immutable Behavior/ABI predecessor identities;
- use the current successor's principal-observation base input-confirm overlay for the new observation layer;
- retain fail-closed fanout and external-card-decision-lifetime anchors;
- fix evidence-hash self-inclusion before the next run;
- no AF coverage promotion.

## Changed files

This checkpoint only. The corrective workflow change is the next atomic package.

## Tests / result

- run `33755201667`: `FAILED` at overlay composition, before Maven/runtime qualification.
- upstream source/artifact/pin checks: PASS.
- behavior qualification result from this run: `UNKNOWN` (not executed).
- principal-observation result from this run: `UNKNOWN` (not executed).

## Known open points

- AF Principal Observation / Hidden Information remains OPEN for `19/21` hidden-required paths.
- Manifest is one hidden-required AF target consumer and remains fail-closed under the current profile classifier unless its actual principal-observation semantics are explicitly adjudicated; no waiver is implied by this overlay failure.

## Exact next step

Update `.github/workflows/ws33-g3-svar-af-principal-observation-v4.yml` so the observation layer applies the current successor `apply-ws33-input-confirm.py` before `apply-ws33-observation-fanout.py`, while retaining the immutable AF runtime overlays for stack/target/SVar behavior; fix `EVIDENCE_SHA256SUMS.txt` self-inclusion in the same atomic correction; allow the resulting commit to trigger a fresh gate and immediately persist its run/source identity.

`LAST_ADJUDICATED_RUN = 33755201667`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
