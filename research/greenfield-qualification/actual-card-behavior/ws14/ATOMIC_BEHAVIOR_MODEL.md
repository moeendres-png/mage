# WS14 atomic behavior-path model

WS14 adds `forge-atomic-path-v1` alongside, and does not replace, WS11 `forge-path-v1` full-script signatures.

## Source authority

For each exact WS11 Oracle identity, the materializer revalidates the pinned Forge source byte hash and recomputes the WS11 full-script signature before deriving atomic bindings. The only implementation-resolution authorities are pinned Forge dispatch structures or explicit parser construction paths. English similarity, card names, keyword text and source presence alone never create a resolved primitive.

Resolved primary domains are:

- `ABILITY_API`: `AB$` / `SP$` / `ST$` / `DB$` API token through pinned `ApiType` to its concrete `SpellAbilityEffect` class.
- `ABILITY_RECORD`: Forge `AbilityFactory.AbilityRecordType` construction path (`AbilityApiBased`, `SpellApiBased`, `StaticAbilityApiBased`, `AbilitySub`).
- `COST`: `AbilityFactory.parseAbilityCost` / card mana-cost construction through `forge.game.cost.Cost`.
- `TARGETING`: `ValidTgts$` through `AbilityFactory.readTarget` / `TargetRestrictions`.
- `TRIGGER`: `T:Mode$` through pinned `TriggerType` to its concrete `Trigger` implementation.
- `REPLACEMENT`: `R:Event$` through pinned `ReplacementType` to its concrete `ReplacementEffect` implementation.
- `STATIC_MODE`: `S:Mode$` through pinned `StaticAbilityMode`.

Script material with no safely resolved implementation dispatch is retained verbatim at token/value provenance level as `binding_status=UNKNOWN`, `evidence_class=UNKNOWN`, with no primitive ID and no owner. In particular, WS14 does not promote keywords, alternate-mode prose, or arbitrary SVar expressions solely because they parse.

## Primitive identity

A primitive ID is deterministic over the exact dispatch domain, dispatch token and resolved implementation target:

`forge-primitive-v1 = SHA256(domain NUL token NUL implementation_target)[0:32 hex]`

The manifest rejects any duplicate primitive ID whose full semantic descriptor differs. Every resolved primitive has exactly one owner family:

- `ACTION_COST_DECISION`
- `TRIGGER_REPLACEMENT_ZONE_SBA`
- `CONTINUOUS_COPY_CONTROL`
- `COMBAT_COMMANDER`
- `HIDDEN_RNG_REPLAY`

This ownership is only a parallel-qualification partition. It does not assert behavior correctness. Cross-family dependencies may be added by successor workstreams without changing primitive identity.

## Per-identity provenance

Every identity row retains Oracle ID/name, exact Forge source path, exact source hashes, all original WS11 full-script signatures, resolved atomic primitive IDs, primitive family, source line/directive/token/value provenance, resolved implementation target, unresolved bindings, and ambiguity status.

## Qualification boundary

WS14 is decomposition and ABI work only. `behavior_qualification=NOT_EVALUATED` and `behavior_pass_issued_from_parsing=false` are invariant outputs. Q6 is not adjudicated here.

WS15–WS19 may qualify a primitive only with a witness conforming to `WS14_WITNESS_ABI.schema.json` and the semantic validator. A witness that names multiple primitives must contain a distinct exercised record for every named primitive, with trace-event and state-assertion references proving actual execution. Stdout-only evidence is invalid.
