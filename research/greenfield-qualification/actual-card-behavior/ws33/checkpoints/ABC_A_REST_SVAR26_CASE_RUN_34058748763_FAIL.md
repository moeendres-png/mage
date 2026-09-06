# WS33 ABC — A-rest SVar26 case projection run 34058748763 — terminal FAIL

Status: **FAIL_CLOSED**
Classification: **CODE_DERIVED projector serialization defect**
Coverage promotion: **FALSE**
Coverage mutated: **FALSE**

## Frozen lineage

- source HEAD: `e01d5d487771ecf6c24827386692d964fbc647f8`
- source TREE: `3a0038a369a466ccab5db5184b3b4fa7fe57f1fe`
- run: `34058748763`
- job: `101555343007`
- topology run: `34002894410`
- topology artifact: `9980023181`
- topology digest: `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- runtime artifact: **NONE** — upload was skipped because projection failed before output completion.

## Terminal evidence

- immutable topology consumption: `SUCCESS`
- topology lineage/digest/gate checks: `SUCCESS`
- projector: `FAIL`
- exact failure: `WS33_A_REST_SVAR_PROJECT=FAIL unsupported first token: Mode$ ChangesZone`

The projector incorrectly applied the SpellAbility first-token parser (`SP$`/`AB$`/`DB$`) to trigger-parent scripts. Actual selected trigger parents are correctly represented by Forge trigger scripts beginning with `Mode$ ChangesZone`, `Mode$ DamageDone`, `Mode$ SpellCast`, or `Mode$ Phase`.

The 21-column trigger runtime ABI does not require a parent SpellAbility API/token; it carries the actual trigger parent script, directive, consumer field and event mode. Therefore parsing a SpellAbility API from a trigger parent is both unnecessary and incorrect.

## Repair boundary

- Parse target SVar scripts as `SP/AB/DB` as before.
- Parse parent API/token only for non-trigger `ABILITY`/`SVAR` parents.
- For `TRIGGER` parents, validate `Mode$ <event>` equals the already-selected topology `event_mode` and serialize the raw parent script unchanged.
- Perform no consumer inference or Magic legality logic.
- Fresh projection run required.
