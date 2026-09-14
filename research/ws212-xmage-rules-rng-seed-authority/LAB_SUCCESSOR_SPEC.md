# WS213 — XMage Consolidated Core Repin and Requalification (Lab successor spec)

Successor to the provisional WS210 concept; the ONE consolidated Commander-Lab
repin/requalification step after WS212. To be executed in Commander-Lab, NOT in
WS212 (no Lab mutation here).

## Inputs (all consumed at exact pins)

- WS212 terminal candidate (this branch HEAD at publication): automatically
  includes WS206 CR510 combat correction + WS211 concession
  availability/action semantics + WS212 Rules-RNG seed contract.
- WS204 B4-D generic legal-action evidence.
- WS205 First-Wave evidence (as available at WS213 time).
- WS208 determinism root-cause evidence (Lab seed ≠ Rules authority).
- WS207 setup authority (if terminal by then).

## Required Lab changes

1. Repin XMage to the exact WS212 terminal candidate (commit + tree).
2. Bind `XmageFullGameSession`'s orchestration seed to the authoritative per-game
   Rules-seed API — `game.setRulesSeed(seed)` immediately after game construction
   and BEFORE `game.start`/`init` — for every game in a credited session.
3. Enable `game.setRequireExplicitSeed(true)` in credited harnesses so a missing
   binding fails closed before shuffle/mulligan/coin/die consumption.
4. STOP relying on `RandomUtil.setSeed` as Rules-seed authority; retain
   `RandomUtil` only for appropriate non-Rules use (AI discretion, UI, infra).
5. Prove `explicit seed_supported` truthfully against the WS212 contract
   (explicit flag true, recorded seed, fail-closed gate armed).

## Requalification battery (no automatic credit)

6. Rerun the WS204 generic-action battery.
7. Rerun D1–D5.
8. Rerun WS208 fresh-process twins (same-seed equality + different-seed control).
9. Re-adjudicate `D5_TWIN_EQUALITY` (stays UNKNOWN until this passes).
10. Run actual multiple-blocker combat through the corrected WS206 path.
11. Expose authoritative CONCEDE as a LegalAction from WS211 core availability —
    no Lab legality heuristics.
12. Rerun G04.
13. Preserve hidden-information scoping.
14. Run affected WS205 twin-matrix / setup scenarios available at that time.
15. Grant no behavior credit automatically.

## Lab burden explicitly NOT satisfiable by WS212 alone

Rerun and re-seal in Lab, with fresh Lab-side evidence, before claiming fixed:

- A03, B01, D06, E02, H01-HUMILITY_FIRST, I01, plus controls.

Rationale: engine-unit determinism does not transfer to Lab behavior credit
without repin + binding + requalification (evidence policy).
