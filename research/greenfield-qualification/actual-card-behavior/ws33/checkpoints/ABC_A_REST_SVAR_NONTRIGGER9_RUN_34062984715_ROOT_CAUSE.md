# WS33 ABC — A-rest SVar runtime routing root cause after run 34062984715

Classification: **DIRECTLY_VERIFIED + CODE_DERIVED**
Primary defect class: **QUALIFICATION CASE ROUTING / FIXTURE LIFECYCLE**
Forge Rules Core defect: **NOT PROVEN**
Coverage promotion: **FALSE**

## 1. Nested `SVAR:DB$` is not a standalone production root

The current SVar26 projector routes every selected parent whose directive is not `TRIGGER` into the AbilityFactory-style NonTrigger ABI when `ability_factory_compatible=true`.

Run `34062984715` proves that this is insufficient. Avengers Quinjet path
`forge-behavior-v2:998c818f96396b9d032dd327a137c613226e93d9` has immediate target parent:

- target SVar `DBReturn`;
- immediate parent SVar `TrigCharm`;
- parent script `DB$ Charm | Choices$ DBChangeZone,DBReturn`.

Pinned Forge source shows `TrigCharm` is consumed in production by **two actual triggers**:

- `Mode$ ChangesZone ... Execute$ TrigCharm`;
- `Mode$ Attacks ... Execute$ TrigCharm`.

The qualification harness instead attempted `AbilityFactory.getAbility(... TrigCharm ...)` as a detached root and crashed before Decision/target reachability. A syntactically AbilityFactory-compatible `DB$` SVar therefore cannot be treated as proof of a standalone production entrypoint.

Repair requirement: runtime routing must recursively resolve the first production consumer of a nested `DB$` selected parent. For this exact source shape that means event/trigger execution, retaining both source-proven trigger entrypoints. Do not patch Avengers Quinjet by name and do not construct the target or parent subability as a standalone production substitute.

## 2. Charm choice legality depends on real target candidates before `makeChoices`

Pinned Forge `CharmEffect.makePossibleOptions` removes a targeted mode when its `TargetRestrictions` has `minTargets > 0` and `getNumCandidates(...) == 0`.

The inherited G fixture seeds libraries/hands plus a narrow battlefield fixture, but no generic public graveyard target inventory. Therefore several A modes are filtered before the authoritative `MODE_SELECTION` request exists:

- Grim Discovery `ChangeCreature`: needs an actor-owned creature card in Graveyard;
- Grim Discovery `ChangeLand`: needs an actor-owned land card in Graveyard;
- Fantastic Elasticity `DBReturn`: needs an actor-owned instant or sorcery card in Graveyard;
- Steel Sabotage `DBChangeZone`: needs an artifact permanent on Battlefield.

The fact that Fantastic Elasticity `DBBounce`, Sublime Epiphany `DBReturn`, and Aether Tradewinds passed under the same engine stack confirms the mechanism itself works where fixture prerequisites exist.

Repair requirement: add a **path-independent public fixture inventory** before parent choices (representative actor-owned Creature, Land, Instant/Sorcery in Graveyard and Artifact/Permanent on Battlefield). Forge remains sole legality/filtering authority. No ValidTgts parser or pilot-side legality inference may be introduced.

## 3. Authoritative modal cardinality must be obeyed while forcing target-path exercise

The G AF harness special-case for a source-proven Charm mode returns immediately after selecting the desired authoritative mode. That is valid only when one selection satisfies the request minimum.

Profane Command exposes a Forge-authoritative `MODE_SELECTION` request requiring two modes (`CharmNum$ 2`). Selecting only the desired `DBSearch` mode produced `INVALID_SELECTION_COUNT`.

Repair requirement: select the desired source-proven option, then deterministically fill only from the **remaining options already present in the authoritative request** until `minimumSelection` is satisfied. Never infer modal legality in the pilot; never exceed `maximumSelection`.

## 4. Fantastic Elasticity mode-identity failure is downstream of missing fixture candidates

`DBReturn` is source-proven exactly once in the parsed Charm parent, but Forge correctly filters it when there is no legal graveyard target candidate. The harness then cannot find its semantic identity in the authoritative `MODE_SELECTION` set and fails closed. The missing public graveyard fixture explains this without any Rules Core defect.

## Repair boundary

The next material changes may only:

1. correct SVar case routing from nested `DB$` parents to their source-proven production consumers;
2. add path-independent public fixture candidates;
3. make the discretionary pilot obey Forge-requested modal cardinality while retaining desired-mode membership checks.

No card-name branches, no target legality parser, no direct `AbilitySub.resolve`, no manual target injection, no detached target SVar execution, no coverage mutation.
