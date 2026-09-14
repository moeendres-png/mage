# WS212 Explicit Seed Contract (engine truth)

## Credited (explicit / replay) mode

1. Construct the game (any `GameImpl`, incl. `CommanderFreeForAll`): a
   nondeterministic default `rulesSeed` is recorded, `isRulesSeedExplicit() == false`.
2. Orchestration calls `game.setRulesSeed(seed)` — resets the `GameRandom` stream,
   the consumption counter (`getRulesRandomCalls() == 0`) and marks explicit.
3. Credited harnesses additionally call `game.setRequireExplicitSeed(true)`.
4. Orchestration calls `game.start(...)` → `init(...)`.
   `init` throws `IllegalStateException` BEFORE any Rules-random consumption when
   explicit mode is required but no explicit seed was supplied.
5. Initial shuffle (`player.shuffleLibrary` → `library.shuffle(game.getRulesRandom())`)
   then consumes the explicit stream; same seed + same inputs ⇒ identical order,
   hands, and counts across fresh JVMs.

## Non-credited (default) mode

- No `setRulesSeed` call: the game runs on its recorded UUID-derived default seed.
- `isRulesSeedExplicit() == false`; `getRulesSeed()` still carries replay identity.
- Default games are NOT promised cross-run reproducibility.

## Non-goals / prohibitions

- `RandomUtil.setSeed(seed)` never becomes Rules authority (separate stream).
- `getRulesRandomCalls()` and the seed getters are diagnostics; they consume nothing.
- Game copies duplicate — never share — RNG state; sibling sims may coincide by design.
- No constructor seed API exists or is needed: the construction→seed→start window
  contains zero Rules consumption, so post-construction binding is complete.

## Qualification

- `Mage/src/test/java/mage/WS212RulesSeedAuthorityTest.java` (8/8) +
  `mage.WS212FreshJvmProbe` (fresh-process twins + control).
- `Mage.Tests/.../ws212/WS212SeededRulesConsumersTest.java` (8/8, live games).
- Fail-closed gate proven BEFORE consumption (`calls == 0` after the throw).
