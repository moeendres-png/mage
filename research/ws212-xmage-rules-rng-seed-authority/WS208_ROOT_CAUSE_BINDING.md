# WS208 Root-Cause Binding (WS212 confirmation)

WS208 (32 fresh-JVM traces, same Lab seed + decks + decision prefix) proved:

- pre-start library order identical;
- `RandomUtil` probe streams identical;
- post-start library order / opening hands / playable sets DIVERGED;
- first divergence before action enumeration; bridge projection
  membership-transparent; no Lab enumeration fix needed.

WS212 binds that root cause to the exact engine call chain at the WS211 base:

1. `XmageFullGameSession` seeds only `RandomUtil.setSeed(seed)` (Lab side,
   NOT mutated here; verified from the read-only WS208 reference root).
2. `GameImpl` constructor builds its Rules stream from an unrelated default:
   `UUID.randomUUID()` → `rulesSeed` → `new GameRandom(rulesSeed)`
   (`Mage/src/main/java/mage/game/GameImpl.java`, L197-199).
3. Initial shuffle calls `PlayerImpl.shuffleLibrary` →
   `library.shuffle(game.getRulesRandom())` (`PlayerImpl.java` L1937-1939,
   `Library.java` L39-49).

Therefore `RandomUtil.setSeed` does not — and must not — control Rules
randomness. The engine already owns the correct authority
(`game.getRulesRandom()` / `setRulesSeed`); the missing piece was never an
engine RNG defect but the orchestration binding (Lab successor burden: bind the
orchestration seed to `Game.setRulesSeed` before `start`/`init`, stop relying on
`RandomUtil.setSeed` as Rules authority).

- `WS208_ROOT_CAUSE_CONFIRMED = YES` (engine-side call chain re-verified at
  WS211 HEAD; Lab-side traces inherited from WS208 evidence, not re-run here).
- No Commander-Lab mutation in WS212.

Evidence class: WS208 traces = DIRECTLY_VERIFIED (Lab, inherited);
engine call-chain binding = CODE_DERIVED (this HEAD).
