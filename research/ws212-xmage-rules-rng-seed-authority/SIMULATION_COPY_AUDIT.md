# WS212 Simulation / Copy Audit

Code (GameImpl copy ctor, L252-259): the copy duplicates RNG state via
`GameRandom.copy()` — independent object starting at the parent's current
position; `rulesSeed`, `rulesSeedExplicit`, `requireExplicitSeed` propagate.
`createSimulationForAI` / `createSimulationForPlayableCalc` operate on copies;
sim RNG is never written back into the parent.

Runtime (DIRECTLY_VERIFIED):

- `WS212RulesSeedAuthorityTest.testSimulationCopyDoesNotPerturbParent`: 50+ sim
  draws on the copy leave the parent count untouched; the parent continues the
  undisturbed control stream.
- `WS212SeededRulesConsumersTest.t8_liveCopyDoesNotPerturbParent`: same on a live
  game (copy inherits seed/explicit/calls; 50 sim draws; parent count unchanged).

Known/documented (by design, not a defect): two sibling copies taken from
identical parent state intentionally start at identical RNG positions
(AI-search heuristic limitation, attested in code). Simulations must therefore
never be mistaken for independent credited replays.

`SIMULATION_PARENT_RNG_ISOLATION = YES`.
