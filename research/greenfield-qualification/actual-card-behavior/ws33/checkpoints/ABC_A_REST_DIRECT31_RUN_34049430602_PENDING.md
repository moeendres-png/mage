# WS33 ABC — A-rest Direct31 mana lifecycle diagnostic — PENDING

Status: **PENDING**
Coverage promotion: **FALSE**
Coverage mutation during witness: **FORBIDDEN**
Run source: **FROZEN**

- source HEAD: `1db6ae137090123bf463b5c9970c70a5a13aed57`
- source TREE: `e052c60f054f1a1c0252123a7e48711f73687076`
- run: `34049430602`
- job: `101530235239`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- expected artifact name: `ws33-abc-a-rest-direct31-runtime-34049430602`
- exact Direct31 paths: `31`
- predecessor topology artifact: `9980023181`
- predecessor coverage: `488 PASS / 3700 UNKNOWN`

Purpose of this run: retain observation-only `InputPayMana.driveExternal()` lifecycle telemetry in addition to the already qualified target/PlaySpellAbility/hidden-observation instrumentation. The observer records authoritative option tokens, selected server-mapped action tokens, remaining `ManaCostBeingPaid`, mana-ability host/id, and terminal paid state. It does not alter option construction, pilot selection, mana/cost state, or any boolean return.

No source on this run may be changed until terminal adjudication. On failure, persist artifact digest and root cause before repair. On success, independently verify Record/Replay/Observation evidence before any coverage promotion.
