# WS33 ABC — A-rest SVar26 case projection run 34058829282 — terminal PASS

Status: **PASS**
Evidence class: **DIRECTLY_VERIFIED artifact + deterministic projection**
Coverage promotion: **FALSE**
Coverage mutated: **FALSE**

## Frozen lineage

- source HEAD: `6dc8a3fb37f91026fb8b75a9614d528f4b88996d`
- source TREE: `45ec21c7c1d17272da194acb3a9ad73ea77f32de`
- run: `34058829282`
- job: `101555560994`
- topology run: `34002894410`
- topology artifact: `9980023181`
- topology digest: `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- output artifact: `9996808331`
- artifact name: `ws33-abc-a-rest-svar26-cases-34058829282`
- artifact digest: `sha256:ea34615a1ee8735b9f97fd1ee3e6e9ff2fa925569792339a90b15fd4f03e99ec`

The downloaded ZIP SHA-256 independently equals the GitHub artifact digest.

## Independent artifact verification

`A_REST_SVAR_CASE_GATE.json`:
- status `PASS`
- SVar paths `26`
- nontrigger paths `9`
- trigger paths `17`
- selected parent entrypoints `26`
- consumer inference performed `false`
- nontrigger ABI columns `19`
- trigger ABI columns `21`
- target implementation `forge.game.spellability.TargetRestrictions`
- RNG nontrigger `0`
- RNG trigger `2`
- coverage mutated `false`
- coverage promotion `false`

Exact trigger mode partition:
- ChangesZone `14`
- DamageDone `1`
- SpellCast `1`
- Phase `1`

Independent checks:
- `a-rest-svar-nontrigger9.tsv`: exactly `9` rows, every row `19` columns
- `a-rest-svar-trigger17.tsv`: exactly `17` rows, every row `21` columns
- union: exactly `26` unique path IDs
- internal `SHA256SUMS`: `8/8` entries verified
- no runtime witness or coverage mutation occurred.

This artifact is the immutable case-identity/parent-input boundary for the fresh A-rest NonTrigger9 and Trigger17 runtime campaigns. It is not Behavior PASS by itself.
