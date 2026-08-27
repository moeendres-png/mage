# Final Engine Scorecard — Qualification Closure 2026-08-27

This is a **fail-closed scorecard**, not a frozen Production Rules Core selection.

| Candidate | Rules/Commander evidence | Decision boundary | Hidden info | Replay/RNG | Isolation | Actual-card closure | Current production status |
|---|---|---|---|---|---|---|---|
| Forge `8c7e9afb...` | Strongest broad mature runtime evidence; 2P–5P and exact RogShai previously qualified | **FAIL at current remote GUI boundary.** Run `33112928078` / artifact `9663315184` proves authoritative Player `validChoices` are not exported and no typed request token exists. Forge Rules Core itself is not rejected; a server-side Input/PlayerControllerHuman Decision Export hook remains plausible. | **NOT PASS**. Raw decoded transport leak count 74; future adapter filtering unproven | **NOT PASS**. RNG census exists; event tape explicitly unqualified | not yet production-qualified | source index/presence available; behavior union incomplete | FINALIST rules core; client-only remote adapter rejected; server-side typed Decision Export is next qualification hypothesis |
| XMage `86d86b58...` | Strong independent Commander/rules evidence | own targeted census says complete external-pilot runtime gate=false | principal-scoped external observation runtime gate=false | incomplete | incomplete | broad card corpus but production behavior closure not established | FINALIST / strong differential reference |
| phase.rs `fae406c...` | Strong typed targeted conformance; prior 49 Commander, 5 topology, 90 visibility, 78 interaction, 22 serialization tests | source externalizable, but all required decisions not externalized/tested | useful visibility evidence, not production external-pilot boundary | incomplete | incomplete | major unimplemented-card surface prevents actual-card closure | typed architecture/reference finalist, not admitted production core |
| Manabrew `754ec2ae...` + Forge `192b5eab...` | 2P–5P java-forge runtime previously qualified; parity/headless evidence | **FAIL** exact-pin audit: first/default/pass fallbacks | incomplete | internal random target not explicit tape | **PASS** concurrent 4P two-game process-isolation run `33090536113` | not closed | headless/parity/isolation reference; current interactive production path rejected |

## Scorecard verdict

No candidate currently satisfies the mandatory production admission contract. The first shared dependency blocker remains `DECISION_EXTERNALIZATION`.

For Forge, the first subgate is now exact rather than generic:

`ENTITY_PLAYER_SELECTION_LEGAL_CHOICE_EXPORT = FAIL` at the current remote GUI boundary.

The minimum proven production-reachable unsupported count is `1`, witnessed by Player-target selection from authoritative `InputSelectEntitiesFromList.validChoices`; Kaervek the Merciless provides a relevant `ValidTgts$ Any` path.

Forge remains the most practical Rules Core candidate because the failure is in the human/remote decision boundary, not a demonstrated Rules Core defect. The next qualification hypothesis is a server-side typed Decision Export hook at authoritative `Input` / `PlayerControllerHuman`, without MTG rules reimplementation. This remains a hypothesis until runtime-qualified.
