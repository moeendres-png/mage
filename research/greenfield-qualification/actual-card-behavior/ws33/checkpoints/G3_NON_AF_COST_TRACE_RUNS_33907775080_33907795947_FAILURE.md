# WS33 G3 non-AF cost-trace diagnostic failure checkpoint

Status: `FAILURE_CHECKPOINT`

Evidence classification: `DIRECTLY_VERIFIED` for GitHub run/job/artifact metadata and job-log failure; `DIRECTLY_VERIFIED` for independent local ZIP SHA256 re-hashes; `CODE_DERIVED` for the diagnostic-anchor classification.

## Source boundary

- branch: `work/ws33-g3-final-closure-20260902`
- diagnostic source HEAD: `2bb3a56a3edcefdd18d0a26bba5755e393ee28e7`
- diagnostic source TREE: `2046196b514ad0bb4e64297fc8de024b0b216170`
- commit message: `ws33 g3: trace TriggeredSources sacrifice cost boundary`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- effective-manifest file SHA256: `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- topology consumer-model SHA256: `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`

## Protocol incident

Exactly one diagnostic source commit unexpectedly produced two push-triggered runs of `.github/workflows/ws33-g3-svar-event-runtime.yml` with the same source HEAD. This violates the WS33 retry discipline of one run per diagnostic/repair commit and is therefore recorded explicitly rather than silently selecting one run.

No third run may be triggered from this source commit.

Both runs failed before Java setup / record execution, so neither run changes the valid runtime evidence from run `33863979003`.

## Run A

- RUN: `33907775080`
- JOB: `101136703588`
- event: `push`
- terminal conclusion: `failure`
- source HEAD: `2bb3a56a3edcefdd18d0a26bba5755e393ee28e7`
- source TREE: `2046196b514ad0bb4e64297fc8de024b0b216170`
- artifact ID: `9950185061`
- artifact name: `ws33-g3-svar-event-runtime-33907775080`
- GitHub digest: `sha256:defe92ec72912fc455496d037f9cb04ceb01c56356b6423fd469947ce2973d73`
- independently downloaded ZIP SHA256: `defe92ec72912fc455496d037f9cb04ceb01c56356b6423fd469947ce2973d73` — exact match
- Steps 1-11: success
- Step 12 `Prepare 33-parent event harness with request trace`: failure
- Steps 13-17: skipped
- Step 18 artifact upload: success
- record campaign: NOT RUN
- Decision/RNG adjudication: NOT RUN
- replay: NOT RUN

Exact first material failure from the job log:

```text
WS33_G_COST_TRACE=FAIL TriggeredSources sacrifice candidates: expected exactly one anchor, got 2
```

The request-trace tool also emitted its general patch success marker, but the process correctly exited non-zero because the cost-trace diagnostic sub-patch failed its strict anchor cardinality check.

## Run B

- RUN: `33907795947`
- JOB: `101136772850`
- event: `push`
- terminal conclusion: `failure`
- source HEAD: `2bb3a56a3edcefdd18d0a26bba5755e393ee28e7`
- source TREE: `2046196b514ad0bb4e64297fc8de024b0b216170`
- artifact ID: `9950194328`
- artifact name: `ws33-g3-svar-event-runtime-33907795947`
- GitHub digest: `sha256:92fc6c1f951ceff8b3e962db3dcadd9d04e03cc95bd47c3cc72f0f6ab2a85544`
- independently downloaded ZIP SHA256: `92fc6c1f951ceff8b3e962db3dcadd9d04e03cc95bd47c3cc72f0f6ab2a85544` — exact match
- Steps 1-11: success
- Step 12 `Prepare 33-parent event harness with request trace`: failure
- Steps 13-17: skipped
- Step 18 artifact upload: success
- record campaign: NOT RUN
- Decision/RNG adjudication: NOT RUN
- replay: NOT RUN

Exact first material failure from the job log:

```text
WS33_G_COST_TRACE=FAIL TriggeredSources sacrifice candidates: expected exactly one anchor, got 2
```

## Adjudication

The two runs are diagnostic-tooling failures, not runtime behavior failures. They never reached Java compilation or the 33-parent campaign. The newly added generic cost-boundary diagnostic searched for an anchor that occurs twice in the generated harness and intentionally failed closed on cardinality `2` instead of mutating an ambiguous location.

Therefore:

- no Forge rules behavior has been newly implicated;
- no fixture/root-cause repair is justified from these runs;
- no previous PASS evidence is invalidated;
- the valid latest runtime state remains run `33863979003`: record `32/32` effective paths PASS, parents `33/33` PASS, Decision `22/22`, RNG `9/10`, replay blocked;
- missing RNG-required path remains `forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d` (`Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`);
- `G3_NON_AF_STATUS = UNKNOWN`;
- `COVERAGE_PROMOTION = FALSE`;
- `WS33_COMPLETE = FALSE`;
- `TASK_COMPLETE = NO`.

## Exact next atomic action

Repair only the generic diagnostic patcher's ambiguous anchor selection in `research/greenfield-qualification/actual-card-behavior/ws33/ws33_instrument_g_authoritative_requests.py`. The repair must select the intended semantic harness site structurally or by a uniquely qualified surrounding context; it must not branch on card name or path ID and must not change Forge rules behavior, fixture semantics, decisions, RNG, targets, costs, coverage, or replay behavior.

Then create exactly one successor run from the repaired diagnostic commit, persist its RUN/JOB/SOURCE_HEAD/SOURCE_TREE immediately, and make no runtime-affecting write until that successor is terminal.
