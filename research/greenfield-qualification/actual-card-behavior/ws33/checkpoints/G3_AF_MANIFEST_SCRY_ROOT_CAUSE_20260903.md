# WS33 G3 AF — Manifest / Scry principal-observation root cause

Status: `ROOT_CAUSE_COMPLETE`

This checkpoint follows `G3_AF_PRINCIPAL_OBSERVATION_RUN_33762514428_FIRST_FAILURE.md` and does not promote coverage.

## Evidence classification

- run/artifact facts: `DIRECTLY_VERIFIED`
- pinned Forge control-flow findings: `CODE_DERIVED`
- Magic semantics below: `EXTERNALLY_RULE_VALIDATED` against the current official Comprehensive Rules effective 2026-08-07
- proposed witness repair: `MODELED` until fresh runtime/ABI/record-replay evidence passes

## Manifest path

Path:
`forge-behavior-v2:47f0f37a5823140c6fe301fc21730cff8d227057`

Actual card/source: Reality Shift.

Executed target SVar:
`DB$ Manifest | DefinedPlayer$ TargetedController`

Pinned Forge `ManifestBaseEffect.manifestLoop` has three shapes:

1. `Choices` / `ChoiceZone`: controller selection;
2. default/explicit `Defined=TopOfLibrary`: automatic top-of-library selection;
3. other explicit `Defined`: targeted/defined cards.

This exact path has no `Choices`, no `ChoiceZone`, and no `Defined`, so pinned Forge takes the default `TopOfLibrary` branch and manifests that card without a card-selection/look decision.

Current CR 701.40 defines manifest as the face-down battlefield transition. The controller's continuing permission to inspect their own face-down permanent is separately provided by CR 708.5 after the transition. Manifest itself does not instruct the player to look at the library card.

Adjudication: this exact source shape is `NEGATIVE_OR_TRANSITION_ONLY`, not `UNKNOWN_HIDDEN_CONSUMER`. The verifier repair must be parameter-shape based. It must not classify all `Manifest` APIs as negative: `Choices`/`ChoiceZone` and other unresolved shapes remain positive/unknown as appropriate.

## Scry path

Path:
`forge-behavior-v2:a817142bdd146d535481895c85387094a2c7ad62`

Actual card/source: Alibou, Ancient Witness.

Executed target SVar:
`DB$ Scry | Defined$ You | ScryNum$ X`

Actual source SVar:
`X:Count$Valid Artifact.YouCtrl+tapped`

Pinned Forge `ScryEffect.resolve` computes `ScryNum` and delegates to `GameAction.scry`. `GameAction.scry` returns immediately when the computed amount is `<= 0`; otherwise it constructs the top-N set and invokes `PlayerController.arrangeForScry(topN)`. Stock `PlayerControllerHuman.arrangeForScry` already calls `tempShowCards(topN)` before the scry choice and `endTempShowCards()` after it.

The failed artifact proves that this campaign execution did not enter the scry choice/observation branch:

- path-level decision event count is `1`;
- the only path-scoped decision event is `TARGET_SELECTION` for the source-parent target;
- there is no Scry/InputConfirm choice event;
- there are no principal observation grants for the path;
- record and replay are identical.

This is consistent with the witness leaving `X=0`: the generic AF fixture does not ensure a tapped artifact controlled by the actor even though the source-proven SVar requires one for a non-zero execution.

Current CR 701.22a requires a player who scries N to look at the top N cards before deciding their destinations; CR 701.22b states that scry 0 creates no scry event. Therefore the failed run does **not** prove a Scry transport defect. It proves that the existing witness did not exercise the positive hidden-information branch required to qualify this actual script.

## Required serial repair

Do not weaken the principal-observation verifier for Scry.

1. Strengthen the AF harness using the actual source-SVar dependency, not the card name. When a target script consumes a source SVar whose expression is `Count$Valid ...+tapped`, establish a deterministic positive witness by tapping an authoritative candidate that satisfies the exact Forge validity expression. The candidate must be selected from actual game state and validated through Forge's own `isValid` predicate; no legality is inferred by the pilot.
2. Run the 21-path AF runtime campaign and retain a new immutable behavior artifact.
3. Rebuild/replay the AF ABI against that exact new behavior artifact/source.
4. Only then repin the principal-observation workflow to the new behavior/ABI evidence.
5. Add the parameter-shape-based Manifest classifier and fail-closed regressions.
6. Run fresh record/replay principal observation. Scry must now produce a complete principal-scoped observation lifecycle. If it does not, only then classify a transport defect.

Because the witness semantics change for a production-reachable hidden-information obligation, the old AF behavior/ABI artifacts remain historical evidence only and must not be reused as the final AF qualification basis.

Coverage promotion: `FALSE`

AF Hidden / Principal Observation: `UNKNOWN`

`WS33_COMPLETE = FALSE`

`TASK_COMPLETE = NO`
