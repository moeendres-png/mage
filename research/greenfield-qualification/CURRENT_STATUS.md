# Commander Simulator Next — Qualification Current Status

Date: 2026-08-27

## Source

- Research branch: `research/greenfield-engine-shootout-20260827`
- Pre-closeout evidence head: `de0720380afa640a85b65011a525498cb6d76267`
- Pre-closeout tree: `f65d495616215c6a7a420cc436afddfcea557652`
- Closeout documentation was then committed incrementally on the same branch.

## Freeze

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`

`READY_FOR_GREENFIELD_BUILD = FALSE`

`READY_FOR_TRUSTED_REAL_DECK_SIMULATION = FALSE`

## Earliest blocking gate

`FIRST_BLOCKING_GATE = DECISION_EXTERNALIZATION`

No finalist has runtime evidence that every production-reachable discretionary player decision crosses a typed external-pilot boundary with exact legal choices, actor/visibility scope, strict response validation and zero fallback.

### Candidate adjudication

- Forge: best broad mature rules/card runtime evidence; stock remote path has forbidden fallbacks; strict research run `33095241142` is incomplete as an exhaustive external-pilot qualification.
- XMage: run `33089884301` passes targeted Commander tests but explicitly records complete external-pilot runtime gate=false and principal-scoped external observation gate=false.
- phase.rs: strong targeted conformance; interaction source is externalizable but all required decisions are explicitly not externalized/tested.
- Manabrew: run `33090536113` passes concurrent 4P process isolation but exact-pin audit finds multiple first/default/pass fallbacks; production decision gate FAIL.

## Other mandatory gates

- Forge 2P–5P Commander runtime and exact RogShai runtime: previous PASS evidence retained, not rerun.
- Hidden information: NOT PASS. Forge raw transport run `33095565820` completed the game but exposed 74 hidden identities; future pilot filtering remains unqualified.
- Semantic replay: NOT RUN to required action-tape + RNG-tape fresh-process A/B/C standard. Forge census explicitly says event-tape runtime unqualified.
- Process isolation: Manabrew candidate-specific concurrent 4P PASS; overall production gate cannot be promoted before a core is frozen.
- Actual-card manifest: INCOMPLETE merged Oracle-identity union; source control counts verified.
- Actual-card behavior coverage: INSUFFICIENT_EVIDENCE; source index/presence is not behavior support.
- Precon extraction: 11/11 exact 100-slot lists extracted successfully in run `33089467077`, artifact `9653672924`; Wizards remains content authority.
- Rules matrices A–T and C01–C22: INCOMPLETE as complete production-boundary matrices; prior passing targeted tests retained.
- Differential: INCOMPLETE under a common explicit action/RNG contract.
- License final decision: DEFERRED until technical architecture is admissible.

## Key domain controls

- Physically held unique identities: 1338.
- Operational own unique identities: 1007.
- RogShai exact 100, normalized hash `2b6258ae1c778784ed252bb46ff828343055177146634c77847506d33f4a4362`.
- Kaervek exact 100, deck hash `aa7a90a4e5cf32f40b1c9832d329aa03f6f7bf130f2d2e9c1e80d10e97c53c7a`.
- Dargo/Tymna theorycraft identities: 743.
- Unknown real opponent slots: at least 142; no synthetic promotion.

## Next action

Implement and run one narrow **research-only Forge Strict External Pilot Qualification Adapter** at exact Forge pin `8c7e9afb8e6caee88644b94e25da5852e36f8928`. It must eliminate Headless auto/default/AI choice behavior, emit a machine-readable Decision Capability Registry, fail closed on every unrepresented path, and prove `SILENT_FALLBACKS=0` plus `PRODUCTION_REACHABLE_UNSUPPORTED_DECISIONS=0` for the actual-card requirement population.

Do not create `commander-simulator-next` before that gate and the downstream mandatory gates pass.
