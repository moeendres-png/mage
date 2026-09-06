# WS33 ABC — A-rest SVar NonTrigger9 runtime run 34062984715 — terminal FAIL

Status: **FAIL_CLOSED**
Evidence class: **DIRECTLY_VERIFIED immutable runtime artifact + independent artifact adjudication**
Coverage promotion: **FALSE**
Coverage mutated during witness: **FALSE**

## Frozen lineage

- source HEAD: `99f674aa9be4f3bedb7060acd7cf374cdce11996`
- source TREE: `4be1c49d5ee2b96984c60dbae88fd123ff4d78e0`
- run: `34062984715`
- job: `101566724160`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- case artifact: `9996808331`
- case artifact digest: `sha256:ea34615a1ee8735b9f97fd1ee3e6e9ff2fa925569792339a90b15fd4f03e99ec`
- runtime artifact: `9998111351`
- artifact name: `ws33-abc-a-rest-svar-nontrigger9-34062984715`
- artifact digest: `sha256:3d00db73831e332c5c953e181f06eaafde499baf19cb0fb78b47b3d6f34471e7`

The downloaded ZIP SHA-256 independently equals the GitHub artifact digest exactly.

## Terminal result

The Maven Record process completed successfully and emitted all 9 exact case summaries. The fresh tape-driven Replay process also completed successfully and emitted all 9 exact case summaries. The final fail-closed adjudication correctly failed because only 3/9 cases were Behavior PASS in each process.

Exact PASS paths in Record and Replay:
- `forge-behavior-v2:a31f4630c06971a5a9c4da7dc7dbef5ee8a8f7b4` — Aether Tradewinds / ChangeZone parent / SubAbility consumer
- `forge-behavior-v2:f2a19455bb1e70147b0c06fd710e6325848e18e3` — Sublime Epiphany / Charm parent / Choices consumer
- `forge-behavior-v2:feb15cc38af1b2d8ffb1f2f3cfe7deb42051aa2e` — Fantastic Elasticity DBBounce / Charm parent / Choices consumer

Exact FAIL paths, identically reproduced in Record and Replay:

1. `forge-behavior-v2:1ccbeda989a96da340b08186248977134c3bb7bc` — Grim Discovery / `ChangeLand`
   - `java.lang.IllegalStateException`
   - `Forge CharmEffect.makeChoices rejected source-proven parent`
   - Decision events `0`; target bind/execute/source-root reachability `0/0/0`.

2. `forge-behavior-v2:7549c1671f9f56f576526e70d918fceedce03cfc` — Grim Discovery / `ChangeCreature`
   - same pre-target `CharmEffect.makeChoices` rejection.

3. `forge-behavior-v2:998c818f96396b9d032dd327a137c613226e93d9` — Avengers Quinjet / `TrigCharm` → `DBReturn`
   - `java.lang.RuntimeException`
   - `AbilityFactory:getAbility: crash when trying to create ability of card: Avengers Quinjet`
   - fails before authoritative Decision/target reachability.

4. `forge-behavior-v2:9c210fe6f626c37c9b3bdd9134a4bfc26dc74fd4` — Fantastic Elasticity / `DBReturn`
   - one Decision request emitted;
   - `ExternalDecisionValidationException: UNSUPPORTED_DECISION_PATH`
   - source-proven target mode identity was not uniquely present in the authoritative `MODE_SELECTION` option set.

5. `forge-behavior-v2:b0d0351f7c2e451972cc5ed513ee0bd0c48a7e6a` — Steel Sabotage / `DBChangeZone`
   - `java.lang.IllegalStateException`
   - `Forge CharmEffect.makeChoices rejected source-proven parent`.

6. `forge-behavior-v2:fa2b8db73866aee9b2f99fdfa6d3f1827063964e` — Profane Command / `DBSearch` → Pump target path
   - one Decision request emitted;
   - `ExternalDecisionValidationException: INVALID_SELECTION_COUNT`
   - selected response cardinality was outside Forge-authoritative bounds.

The artifact gate reports `FAIL_CLOSED`, `failure_count=46` because each underlying runtime failure also triggers the expected secondary missing-decision/reachability assertions in Record and Replay plus incomplete decision-path coverage. No positive hidden-observation lifecycle was emitted because the six failed paths do not reach the relevant target execution; this run therefore does not qualify Hidden evidence for the 9-path campaign.

## Root-cause classification

Current classification: **HARNESS / FIXTURE / PARENT-LIFECYCLE GAPS; FORGE RULES CORE DEFECT NOT PROVEN**.

The inherited G3 AF harness mechanism is valid for three of these A cases but does not yet establish all production prerequisites for the remaining parent shapes. The failures are deterministic under replay and group into four repair classes:

- Charm production prerequisites / mode-choice lifecycle: Grim Discovery x2, Steel Sabotage;
- parent SVar materialization: Avengers Quinjet;
- source-proven mode identity matching against authoritative mode options: Fantastic Elasticity DBReturn;
- announced-X / authoritative mode-cardinality prerequisites: Profane Command.

No card-name production hacks, pilot-side mana/target/mode rules, direct target-SVar entry, manual target injection, or direct effect resolution are permitted as repairs. Investigate the exact pinned-Forge parent lifecycle for these four classes and repair qualification fixtures/systemic boundary handling only where source-derived.

No PASS path from this failed shard is promoted independently. The exact NonTrigger9 campaign remains unqualified as a whole.
