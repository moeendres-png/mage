# WS33 G3 non-AF — Runtime Freeze — RUN 33928315020 PASS

STATUS = PASS
G3_NON_AF_RUNTIME = PASS
G3_NON_AF_REPLAY = PASS
G3_NON_AF_DECISION_RUNTIME = PASS
G3_NON_AF_RNG_RUNTIME = PASS
G3_NON_AF_PRINCIPAL_OBSERVATION = NOT_YET_PROMOTED
G3_NON_AF_SEPARATE_CERTIFICATION = NOT_YET_RUN
COVERAGE_PROMOTION = FALSE
WS33_COMPLETE = FALSE
TASK_COMPLETE = NO

## Frozen runtime identity

- branch: `work/ws33-g3-final-closure-20260902`
- repair source HEAD: `2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7`
- repair source TREE: `fbb9565d4583db655872cfd378831711b0989b7a`
- workflow: `.github/workflows/ws33-g3-svar-event-runtime.yml`
- workflow run: `33928315020`
- job: `101201530278`
- run attempt: `1`
- exact-source run cardinality: `1`
- terminal conclusion: `success`
- artifact ID: `9957712911`
- artifact name: `ws33-g3-svar-event-runtime-33928315020`
- GitHub artifact digest: `sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b`
- independently downloaded ZIP SHA256: `2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b`
- artifact ZIP size: `369109` bytes

Evidence classification for run/job/source/artifact/digest/independent ZIP SHA256: **DIRECTLY_VERIFIED**.

## Immutable source chain inside artifact

Artifact `diagnostic/SOURCE_CHAIN.json` reports:

- schema `commander-simulator-next.ws33-g-svar-event-runtime.v1`
- status `PASS`
- workflow source HEAD `2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7`
- workflow source TREE `fbb9565d4583db655872cfd378831711b0989b7a`
- Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- direct runtime source HEAD `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`
- topology source HEAD `4032d9c14dc7840e2518a92273037aaba443ada9`
- topology artifact `9866293827`
- topology artifact digest `sha256:6a41f66937b4bf1bcf782045d869ece183c0be49b345eac654dc3588cb98b96b`
- topology consumer-model SHA256 `82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48`
- effective-manifest file SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- effective paths `32`
- parent entrypoints `33`
- `record_replay_equal=true`
- trigger legality authority `FORGE_TRIGGER_HANDLER`
- `target_direct_entry=false`
- `principal_observation_promoted=false`
- `coverage_mutated=false`

The downloaded artifact's top-level `SHA256SUMS` independently verifies every retained source/record/replay/diagnostic/overlay evidence file.

Evidence classification: **DIRECTLY_VERIFIED**.

## Runtime Record gate

GitHub Actions Step 14 `Execute 33-parent record campaign`: `success`.

GitHub Actions Step 15 `Adjudicate record behavior and minimum Decision/RNG obligations`: `success`.

The exact Step-15 gate requires:

- 33 source-parent case rows with 21 fields;
- 32 unique effective paths;
- 33 parent-summary rows with 16 fields;
- every parent `PASS`, exactly one runtime execution, exactly one success, and at least one resolved path;
- 32 case-summary rows exactly matching the unique path set;
- every effective path `PASS`, at least one runtime hit, at least one resolution hit, and zero runtime failure count;
- every Decision-required path must have an `ACCEPTED` decision event;
- every RNG-required path must have an RNG event.

Independent artifact recomputation gives:

- non-AF effective paths: `32/32 PASS`
- source parents: `33/33 PASS`
- Decision-required paths: `22`
- Decision-required missing: `0`
- RNG-required paths: `10`
- RNG-required missing: `0`
- record process `game_completed=true`
- record process `path_count=32`
- record process `pilot_visible_hidden_info_leaks=0`
- record process `cross_principal_decision_leaks=0`
- record process `phase_mismatches=0`
- record process `outer_failure=null`

Evidence classification: **DIRECTLY_VERIFIED**.

## Former blocker — direct closure evidence

Effective path:

`forge-behavior-v2:24a5352cfaa6ae913df6549ceed0c447d526e89d`

Lineage:

`Descendants' Fury -> DamageDoneOnce -> TrigDigUntil -> DigUntil`

The exact successful record now exposes for `ENTITY_LIST_SELECTION`:

- min/max `1/1`
- principal-scoped request
- `cancelAllowed=true`
- response schema `commander-simulator-next.entity-selection.v1`
- option count `1`
- sole authoritative option ID `card:388`
- Decision event `ACCEPTED`

The cost trace now records:

```text
CANDIDATES required=1 mandatory=false sources=388 candidates=388 candidateCount=1
SELECTION cancelled=false selectedCount=1 selected=388
DECISION decisionNull=false
RESULT result=true reason=PAY_AS_DECIDED
```

The same effective path now has RNG event:

- RNG stream `ws31-hidden-rng-replay-4p`
- operation `rules.forge.game.ability.effects.DigUntilEffect.collections_shuffle.1`
- bound `31`

This directly closes the prior `DECISION_NULL -> PAY_COST=false -> RNG missing` runtime chain without card-name/path-ID branching, singleton autopick, first/default/random/pass/cancel fallback, rules mutation, RNG mutation, or coverage mutation.

Evidence classification: **DIRECTLY_VERIFIED** for request/cost/RNG record facts; repair-boundary interpretation remains **CODE_DERIVED**.

## Tape-driven Semantic Replay gate

GitHub Actions Step 16 `Execute tape-driven replay campaign`: `success`.

The workflow requires byte equality between Record and Replay for:

- `case-summary.tsv`
- `parent-summary.tsv`
- `decision-tape.tsv`
- `decision-events-with-path.tsv`
- `rng-tape.tsv`
- `rng-events-with-path.tsv`
- `decision-requests-with-path.tsv`

Independent local comparisons confirm equality for the retained semantic summaries and tapes; the workflow additionally confirmed equality for the event/request path tables.

Replay process reports:

- `game_completed=true`
- `path_count=32`
- `pilot_visible_hidden_info_leaks=0`
- `cross_principal_decision_leaks=0`
- `phase_mismatches=0`
- `outer_failure=null`

Replay Maven test:

- tests `1`
- failures `0`
- errors `0`
- skipped `0`
- `BUILD SUCCESS`

The informational network `DeltaSync` initial-state `Fallback to full state` messages in record/replay are Forge transport synchronization messages, not Decision/Pilot fallbacks; they occur symmetrically and do not alter the strict external-decision contract.

Evidence classification: **DIRECTLY_VERIFIED**.

## Runtime freeze adjudication

`G3.1 Runtime Record = PASS`

`G3.2 Tape-driven Replay = PASS`

`G3.3 Runtime Freeze = PASS`

Frozen tuple:

```text
HEAD     2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7
TREE     fbb9565d4583db655872cfd378831711b0989b7a
RUN      33928315020
JOB      101201530278
ARTIFACT 9957712911
DIGEST   sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b
```

This freezes runtime evidence only. It does **not** promote G coverage and does **not** complete non-AF G3 because the contract still requires:

1. G3.4 separate ABI / Decision / RNG / Replay certification consuming this exact runtime artifact;
2. G3.5 non-AF Hidden31 Principal Observation qualification;
3. only then G3.6 G81 closure using immutable Direct28 + AF21 + this non-AF32 evidence.

## Next action

Read-only inspect the existing G3 certification / Principal Observation tooling and bind it to immutable runtime artifact `9957712911` / digest `sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b`. Do not reconstruct runtime evidence from another run. Do not promote G coverage before both remaining certifications PASS.
