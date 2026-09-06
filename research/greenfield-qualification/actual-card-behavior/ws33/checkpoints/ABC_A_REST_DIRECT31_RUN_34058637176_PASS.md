# WS33 ABC — A-rest Direct31 runtime v6 run 34058637176 — terminal PASS

Status: **PASS**
Evidence class: **DIRECTLY_VERIFIED immutable runtime artifact + independent artifact adjudication**
Coverage promotion: **FALSE**
Coverage mutated during witness: **FALSE**

## Frozen lineage

- source HEAD: `8a1f89d146b33b5539047bddffae196c8fada680`
- source TREE: `4a75e4711c16814434b156c7ccba01148dbab69a`
- run: `34058637176`
- job: `101555047425`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- topology artifact: `9980023181`
- topology digest: `sha256:053ca7036eec2e13dd66022975a7f766e9c8c9ebc3cc30576ab03eaab99cb995`
- runtime artifact: `9996822769`
- artifact name: `ws33-abc-a-rest-direct31-runtime-34058637176`
- artifact digest: `sha256:51ef91bd571662d951c526b38b480fd3fe3a4791fa18394295bdd19547b95b39`

The downloaded ZIP SHA-256 independently equals the GitHub artifact digest exactly.

## Independent artifact verification

All entries in artifact-root `SHA256SUMS` verify.

Exact case identity:
- source rows: `31`
- unique source path IDs: `31`
- record path IDs: `31`
- replay path IDs: `31`
- source == record == replay exact path-ID set: `TRUE`

`DIRECT31_RECORD_GATE.json`:
- status `PASS`
- exact paths `31`
- failures `0`
- remote actor slot `1`
- principal observation instrumented `true`
- play-stage observer `true`
- coverage mutated `false`
- coverage promotion `false`

`DIRECT31_RUNTIME_GATE.json`:
- status `PASS`
- spell paths `24`
- activated paths `7`
- decision-required `31`
- RNG-required `2`
- hidden-required `31`
- replay-required `31`
- actual-card source-bound `true`
- PlaySpellAbility authoritative `true`
- manual target injection `false`
- direct effect resolution `false`
- semantic replay equal `true`
- failures `0`
- coverage mutated `false`
- coverage promotion `false`

Independent per-path checks additionally confirmed for both Record and Replay:
- every case status `PASS`;
- required Decision evidence present;
- required RNG evidence present;
- stack/source-root evidence present;
- runtime hidden-leak delta `0`;
- cross-principal leak delta `0`;
- Record/Replay semantic digests equal.

`DIRECT31_PRINCIPAL_OBSERVATION_GATE.json`:
- status `PASS`
- failures `0`
- Record events `1964`
- Replay events `1964`
- each run: `491 SERVER_GRANT`, `491 CLIENT_VISIBLE`, `491 SERVER_REVOKE`, `491 CLIENT_HIDDEN`
- unauthorized hidden leak required `0`
- cross-principal leak required `0`
- server reasons included in semantic equality;
- client transport `delta:<n>` sequence metadata shape-validated but excluded from semantic equality;
- rules mutation `false`.

Source-chain evidence binds this artifact to the exact frozen source and topology artifact. Overlay evidence confirms:

`WS33_MANA_CANCEL_BOUNDARY=PASS cancel_encoding=REQUEST_LEVEL ordinary_cancel_option=FALSE`

`WS33_MANA_CANCEL_RULES_MUTATION=0 payment_transition_filter=FORGE payment_revalidation=FORGE`

and the PlaySpellAbility/mana observer reports no semantics, boolean, option, selection, mana, or cost mutation.

## Qualification boundary

This is Behavior PASS evidence for the exact Direct31 campaign only. It does **not** promote WS33 coverage by itself. A-rest still requires the fresh SVar NonTrigger9 and Trigger17 runtime campaigns plus A-rest cross-qualification before any serial successor may promote the exact remaining A57 paths.
