# WS20 — actual-path failure adapters: action + rules

`WORKSTREAM_COMPLETE = TRUE`

## Provenance

- `BRANCH = work/ws20-failure-action-rules-20260829`
- `BASE_SHA = 80743bdbc2950b00e422f3deb38f04111f30a4d4`
- `BASE_TREE = 9a2a52932a0d69dcf06c2392cddcf40b47e810cc`
- `FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928`
- `HANDOFF_COMMIT = SELF`; the final branch tip and its qualification run are reported externally because a commit cannot contain its own hash.

## Scope and ownership

WS20 closes exactly:

- `ACTION_NOT_COMPLETABLE`
- `UNSUPPORTED_RULES_PATH`

It does not modify shared WS12 gate/schema files and does not bind or reclassify the other five WS12 production-facing gaps.

Changed only:

- `.github/workflows/ws20-failure-action-rules.yml`
- `research/greenfield-qualification/failure-semantics/adapters/action-rules/**`
- `research/greenfield-qualification/WS20_HANDOFF.md`

`commander-simulator-next.failure-outcome.v1` is retained unchanged.

## ACTION_NOT_COMPLETABLE

Production binding:

`PlayerControllerHuman.chooseExternalEntities -> Ws20ActionCompletionBoundary -> InputSelectEntitiesFromList.applyExternalSelection`

After a response has passed the retained WS01 server-owned validator, WS20 revalidates the selected engine identity immediately before the authoritative Input applies the selection. A selected player must still be in the game. A selected card must still resolve as the current engine card state with the same game timestamp and a current zone. The production overload derives a `completable` boolean from that live engine state and invokes the exact central `requireCompletable(..., completable)` guard before `applyExternalSelection`.

The fault witness invokes that same central production guard with `completable=false`; it does not construct an enum or use a test-only throwing helper. Failure therefore occurs before downstream Input mutation and cannot coerce to first/default/random/pass/cancel.

Required evidence:

- `production_binding = ACTUAL_RUNTIME_PATH`
- `classification = PASS`
- `evidence_class = TECHNICALLY_CONFORMANT`
- exact production guard fault-injected
- emitted category = `ACTION_NOT_COMPLETABLE`
- game / decision / principal context retained
- `state_committed = false`
- downstream mutation sentinel unchanged
- public payload hidden marker count = `0`

## UNSUPPORTED_RULES_PATH

Production binding:

`GameAction.changeZone -> documented Astrotorium merged-object unresolved rules branch -> Ws20RulesPathBoundary`

The exact Forge pin already documents the merged Attraction/Contraption zone-change combination as unresolved in the Rules Core. Inside that branch, `GameAction.changeZone` now passes the live Rules Core condition `c.hasMergedCard()` into the exact `requireSupportedAstrotoriumMergedZoneChange(..., mergedObject)` guard before the existing junkyard action. Normal non-merged Astrotorium behavior remains unchanged. A merged object fails closed instead of continuing through approximate rule handling.

The fault witness invokes that same production Rules Core guard with `mergedObject=true`; no pilot or adapter supplies a substitute resolution, and no default/skip/cancel value is returned.

Required evidence:

- `production_binding = ACTUAL_RUNTIME_PATH`
- `classification = PASS`
- `evidence_class = TECHNICALLY_CONFORMANT`
- exact Rules Core production guard fault-injected
- emitted category = `UNSUPPORTED_RULES_PATH`
- game / principal context retained; no fabricated decision id
- `state_committed = false`
- downstream mutation sentinel unchanged
- public payload hidden marker count = `0`

## Qualification contract

The final branch-tip workflow must prove simultaneously:

- exact base/tree and WS20 ownership verification
- exact Forge pin checkout
- WS01 strict overlay application
- WS12 outcome overlay application
- WS20 overlay application
- exact-pin Forge reactor `test-compile` success
- retained Q1 validator regression PASS
- retained WS12 failure-semantics regression PASS
- WS20 exact production-guard fault witnesses PASS
- machine-readable ACTION and RULES traces conform to `commander-simulator-next.failure-outcome.v1`
- both category rows are `ACTUAL_RUNTIME_PATH / PASS / TECHNICALLY_CONFORMANT`
- all WS20 hard-gate booleans are true
- `other_ws12_unbound_categories_touched = []`
- `FAILURE_SEMANTICS_OVERALL_CLAIMED = false`

Earlier green WS20 runs that exercised weaker direct throwing helpers are superseded by the final exact-production-guard qualification and are not canonical completion evidence.

## Adjudication

When the final branch-tip workflow satisfies the contract above:

- `WS20 = PASS`
- `WORKSTREAM_COMPLETE = TRUE`
- `FAILURE_SEMANTICS_OVERALL_CLAIMED = FALSE`

WS20 does **not** claim overall `FAILURE_SEMANTICS` PASS. The remaining five WS12 production-binding gaps remain outside this workstream.
