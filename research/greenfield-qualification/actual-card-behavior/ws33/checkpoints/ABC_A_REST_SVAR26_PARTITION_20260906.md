# WS33 ABC — A-rest SVar26 exact production-parent partition

Status: **READ_ONLY_PARTITION_COMPLETE**
Evidence class: **DIRECTLY_VERIFIED from immutable A-rest topology artifact**
Coverage promotion: **FALSE**
Coverage mutation: **FALSE**

Source topology gate:

- run `34002894410`
- artifact `9980023181`
- digest `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- topology source HEAD `60fa4ff1b224ede4983087a9c28bb6bbc89c728c`
- topology source TREE `88f5d5460f10364a20d03e8c37854a7793eb00c0`

The immutable `A_REST_TOPOLOGY.json` contains exactly 26 SVar paths and exactly one selected production-reachable parent for each. No unresolved or ambiguous parent remains.

## Partition

### Trigger / Execute — 17 paths

- `ChangesZone`: 14
- `DamageDone`: 1
- `SpellCast`: 1
- `Phase`: 1

Every path is entered through the actual card's selected trigger parent and production TriggerHandler/event path. The target SVar must never be invoked directly. Exact target reachability must be observed at non-fizzled stack resolution.

RNG-required trigger paths:

- `forge-behavior-v2:50445646c41551f1925350dd746c5e8e01353874` — Singe-Mind Ogre
- `forge-behavior-v2:b56b8f8b9c2849358181071bb9413864f584efd2` — Power Pack

### Non-trigger source parents — 9 paths

- `ABILITY:Choices`: 7
- `SVAR:Choices`: 1
- `ABILITY:SubAbility`: 1

Exact non-trigger cases:

1. Grim Discovery — `ChangeLand` — `ABILITY:Choices`
2. Grim Discovery — `ChangeCreature` — `ABILITY:Choices`
3. Avengers Quinjet — `DBReturn` — `SVAR:Choices` via parent SVar `TrigCharm`
4. Fantastic Elasticity — `DBReturn` — `ABILITY:Choices`
5. Aether Tradewinds — `DBChange` — `ABILITY:SubAbility`
6. Steel Sabotage — `DBChangeZone` — `ABILITY:Choices`
7. Sublime Epiphany — `DBReturn` — `ABILITY:Choices`
8. Profane Command — `DBSearch` — `ABILITY:Choices`
9. Fantastic Elasticity — `DBBounce` — `ABILITY:Choices`

These must use actual source-parent binding. Choice parents must traverse Forge's own production choice/mode route and accept only an authoritative option identity corresponding to the source-proven target. The target SVar must never be directly entered.

## Fresh-evidence requirement

Historical G3 SVar-AF/trigger PASS results are infrastructure/reference only. A-rest requires fresh executions for these exact 26 path IDs against the current A-rest topology artifact and the pinned Forge source.

Both campaigns must retain Decision evidence, principal-scoped Hidden Information evidence where required, controlled RNG for the two trigger paths above, and fresh semantic replay. Unsupported or unmaterializable paths remain fail closed.

No partial A promotion is allowed: Direct31 + non-trigger9 + trigger17 must cross-certify as the exact 57-path A-rest union before any serial successor changes coverage.
