# WS20 — actual-path failure adapters: action + rules

`WORKSTREAM_COMPLETE = TRUE`

## Provenance

- `BRANCH = work/ws20-failure-action-rules-20260829`
- `BASE_SHA = 80743bdbc2950b00e422f3deb38f04111f30a4d4`
- `BASE_TREE = 9a2a52932a0d69dcf06c2392cddcf40b47e810cc`
- `FORGE_PIN = 8c7e9afb8e6caee88644b94e25da5852e36f8928`
- `IMPLEMENTATION_HEAD = d6b2ad71691a2733c85ae9198a7a47cb971e2ed6`
- `IMPLEMENTATION_TREE = b09bad290265e709f6c03dd7b5af6173a980ce1c`
- `HANDOFF_COMMIT = SELF`; the final branch tip containing this handoff is reported externally because a commit cannot contain its own hash.

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

After a response has passed the retained WS01 server-owned validator, WS20 revalidates the selected engine identity immediately before the authoritative Input applies the selection. A selected player must still be in the game. A selected card must still resolve as the current engine card state with the same game timestamp and a current zone. A failure throws a typed WS20 failure signal before `applyExternalSelection`; it does not coerce to first/default/random/pass/cancel.

Qualification:

- `production_binding = ACTUAL_RUNTIME_PATH`
- `classification = PASS`
- `evidence_class = TECHNICALLY_CONFORMANT`
- injected not-completable boundary returned `ACTION_NOT_COMPLETABLE`
- `game_id = forge-game:77`
- `decision_id = 41`
- `principal_id = 3`
- `state_committed = false`
- downstream mutation sentinel remained unchanged
- public payload hidden marker count = `0`

## UNSUPPORTED_RULES_PATH

Production binding:

`GameAction.changeZone -> Astrotorium merged-object unresolved rules branch -> Ws20RulesPathBoundary`

The exact Forge pin already documents the merged Attraction/Contraption zone-change combination as unresolved in the Rules Core. WS20 leaves the normal Astrotorium junkyard path unchanged, but when that explicitly unresolved branch is reached for a merged object it now fails closed instead of continuing through the approximate rule handling.

Qualification:

- `production_binding = ACTUAL_RUNTIME_PATH`
- `classification = PASS`
- `evidence_class = TECHNICALLY_CONFORMANT`
- injected unsupported-rule boundary returned `UNSUPPORTED_RULES_PATH`
- `game_id = forge-game:77`
- `decision_id = null`
- `principal_id = 3`
- `state_committed = false`
- downstream mutation sentinel remained unchanged
- public payload hidden marker count = `0`

## Qualified evidence

Implementation qualification run:

- `RUN_ID = 33253558097`
- `JOB_ID = 99103272026`
- `ARTIFACT_ID = 9715133754`
- `ARTIFACT_DIGEST = sha256:8b0e8a38a7ac77069d79bae789bd60e7f70ed1aa0e729cebb07b53b6d03a4795`

Key retained evidence:

- exact base/tree and ownership verification: PASS
- WS01 strict overlay application: PASS
- WS12 outcome overlay application: PASS
- WS20 overlay application: PASS
- `mvn -B -DskipTests -pl forge-gui -am test-compile`: `BUILD SUCCESS`
- retained Q1 probe: `JAVA_EXTERNAL_DECISION_CONTRACT=PASS`
- retained WS12 probe: `WS12_JAVA_FAILURE_SEMANTICS=PASS`
- WS20 Java fault probe: `WS20_FAILURE_ADAPTERS=PASS`
- `WS20_HARD_GATE=PASS`

Artifact file hashes from run `33253558097`:

- `WS20_GATE.json` = `sha256:2a25f75757d2447c9068f35fa7a8ea1eaf321a8c8ab436fa1bcb1e54cc0a8b35`
- `ACTION_NOT_COMPLETABLE_TRACE.json` = `sha256:6346e93dd815805886965abebd201d24be159d9ba10792a579dd8c5a3820e5c5`
- `UNSUPPORTED_RULES_PATH_TRACE.json` = `sha256:2aa39396b5633f6c5bc6762f1f1dff6e270f47ec2b8af45a976a54fbdc9d882f`
- `forge-test-compile.log` = `sha256:09f5f731f26e1142a5699959dae778cc41ee5000511d217bfc0f798321c24767`
- `ws20-java-contract.log` = `sha256:075b6ba1b9e0751b96a0236d6ac1a1f871a1c15319d452b576f2a1638fce748d`

## Hard-gate adjudication

Both owned categories satisfy simultaneously:

- `production_binding = ACTUAL_RUNTIME_PATH`
- `classification = PASS`
- `evidence_class >= TECHNICALLY_CONFORMANT`
- actual fault/condition injection present
- prohibited downstream state mutation absent
- silent fallback/coercion absent
- public failure payload hidden-information safe

Therefore:

- `WS20 = PASS`
- `WORKSTREAM_COMPLETE = TRUE`
- `FAILURE_SEMANTICS_OVERALL_CLAIMED = FALSE`

WS20 does **not** claim overall `FAILURE_SEMANTICS` PASS. The remaining five WS12 production-binding gaps remain outside this workstream.
