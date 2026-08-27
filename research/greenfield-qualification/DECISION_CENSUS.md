# Decision Census — Closeout

Status: **INCOMPLETE; production gate not passed**.

- **Forge:** stock remote path has 10 forbidden fallback signatures. Strict qualification run `33095241142` proved selected null/type rejection but did not prove every production-reachable decision. Its external client still used Headless auto/default behavior and the 2P path later stalled on an additional UI/selection path.
- **XMage:** targeted run `33089884301` is useful Rules evidence, but its own census records `complete_external_pilot_runtime_gate=false` and `principal_scoped_external_observation_runtime_gate=false`.
- **phase.rs:** interaction surface is source-externalizable, but all required decisions are explicitly not externalized-and-tested.
- **Manabrew:** run `33090536113` found multiple current exact-pin silent/default/first-choice fallbacks; production decision gate FAIL.

## First blocker

`FIRST_BLOCKING_GATE = DECISION_EXTERNALIZATION`

Minimal next qualification work: create a Forge exact-pin **research-only Strict External Pilot Boundary** that contains no Headless auto-choice/AI fallback, emits a machine-readable capability registry, rejects missing/stale/wrong-actor/malformed/illegal responses, and runtime-covers every production-reachable decision kind for the actual-card requirement population. Only after that gate passes should Hidden-Info and tape replay be promoted through the same boundary.
