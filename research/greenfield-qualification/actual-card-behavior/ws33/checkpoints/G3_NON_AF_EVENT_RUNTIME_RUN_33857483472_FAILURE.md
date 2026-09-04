# WS33 G3 non-AF event runtime — run 33857483472 failure

Status: `FAIL / BEHAVIOR-BEARING DIAGNOSTIC / NO COVERAGE PROMOTION`

## Immutable identity

- run: `33857483472`
- job: `100974029659`
- source HEAD: `271049e28cd48992babf0872f902d28eddeb9166`
- source TREE: `7798692c9574d472303dd75df3e0534594a9dc7b`
- artifact: `9930890226`
- artifact digest: `sha256:96620d8dd77e23b1092e002b3537cc8b38880c92b60d7fcb38f471353623a261`
- independently downloaded ZIP SHA256: `96620d8dd77e23b1092e002b3537cc8b38880c92b60d7fcb38f471353623a261` — exact match

## Step adjudication

- Steps 1–14: PASS
- Step 15: FAIL
- replay/source-chain: SKIPPED
- evidence upload: PASS

Strict record result remains `32/33` production parents PASS and `31/32` effective paths PASS. Sole failure remains Study Hall `TrigSpent -> TrigScry`, admission/binding/execution `0/0/0`.

## First material failure

Observation-only performTest telemetry identifies the intended commander-spell invocation as:

`WS33_TRIGGER_PERFORM VALID_ACTIVATING_PLAYER false`

with:

- cast `Serra Angel`
- `castCommander=true`
- cast owner id `1`
- SpellCast activator id `1`
- remembered count `1`
- remembered identity matches `1`
- remembered contains current SpellAbility `true`

No `VALID_CARD` or `TRIGGERS_WHEN_SPENT_REMEMBERED` failure occurs first; `ValidActivatingPlayer$ You` is the direct first failing predicate.

The separately persisted root-cause checkpoint `G3_NON_AF_STUDY_HALL_ACTIVATOR_ROOT_CAUSE_20260904.md` derives this from the fixture's missing activating-player context on the source-proven mana producer SpellAbility.

`G3_NON_AF_STATUS = UNKNOWN`
`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
