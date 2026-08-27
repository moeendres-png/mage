# Existing Run Reconciliation — 2026-08-27

Research input head before closeout writes: `de0720380afa640a85b65011a525498cb6d76267`.

| Candidate/gate | Pin | Run | Artifact | Status | Classification | Rerun |
|---|---|---:|---:|---|---|---|
| Forge baseline 2P–5P Commander + RogShai | `8c7e9afb8e6caee88644b94e25da5852e36f8928` | prior qualified runs | prior artifacts | PASS | runtime evidence already established | NO |
| Forge strict remote | same | `33095241142` | workflow evidence | INSUFFICIENT_EVIDENCE | null/type rejection exercised, but Headless auto/default controller remained; 2P stalled on further UI/selection path and 3P–5P did not establish complete external decision coverage | NO full rerun; replace only missing boundary test |
| Forge raw hidden transport | same | `33095565820` | `9656277015` | FAIL | rules game completed; decoded transport exposed 74 hidden identities. This is a real backend-boundary finding, not a build failure. Pilot-visible safety remains unproven. | NO |
| Forge decision/RNG census | same | `33095873712` | `9656344793` | PASS as census only | 109 abstract PlayerController methods; 15 blocking remote decisions; 10 stock forbidden fallbacks; 8 direct rules-game RNG bypasses; event-tape runtime not qualified | NO |
| Forge neutral card index | same | `33090672334` | `9654200891` | PASS as source index only | presence/script index; not behavior coverage | NO |
| XMage targeted v2 | `86d86b580cd7e1f30b51110d70cecae18c1ce452` | `33089884301` | `9655841512` | PASS targeted rules / INSUFFICIENT_EVIDENCE production boundary | own source status: complete external-pilot runtime gate=false; principal-scoped external observation runtime gate=false | NO |
| phase.rs targeted | `fae406c4603f450797014f3ac8e8818b3d36c2a4` | `33078715204` | `9649312620` | PASS targeted groups; HARNESS_FAILURE inventory step | non-empty Commander/topology/visibility/interaction groups pass; `zero commander tests enumerated` came from bad inventory filter. Interaction census says all required decisions not externalized/tested. | NO |
| Manabrew decision/isolation | `754ec2aeec495d67d7bb9b89d0fd67ee22281b46` + Forge `192b5eab000069bbb8917a5df9d60d4a9128aa07` | `33089841571` | evidence artifact | mixed | setup/protocol validation pass; supported-scenario step failed; later missing isolation work separated | NO |
| Manabrew isolation-only | same | `33090536113` | `9654315901` | PASS isolation / FAIL decision gate | concurrent 4P process isolation passed. Exact-pin audit found first-target, first-N discard, first replacement/static, random target, prompt-0 pass and interrupted-priority pass fallbacks. | NO |
| 11 precon extraction | Forge pin | `33089467077` | `9653672924` | PASS extraction | exactly 11 decks, each 100 slots; Forge is extraction helper only, Wizards remains content authority | NO |

## Dependency verdict

The earliest common blocking gate is **DECISION_EXTERNALIZATION**. No current finalist has positive runtime evidence that every production-reachable discretionary decision crosses a typed, actor-scoped, validated external-pilot boundary with zero silent fallback.

Downstream `HIDDEN_INFO`, `REPLAY`, and behavior-level `ACTUAL_CARD_COVERAGE` cannot be promoted to production PASS until that boundary exists and is testable.
