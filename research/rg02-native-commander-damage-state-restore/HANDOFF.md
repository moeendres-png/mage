# RG-02 — Native Commander Damage State Restore Qualification

## Final Handoff — 2026-09-24

**Disposition:** `RG02 = PASS` / `QUALIFICATION_CLOSURE_NO_PRODUCTION_CHANGE`

**Architecture Freeze:** `NOT CLAIMED`

**Production Provider:** `NOT SELECTED`

**WORKTREE:** `NOT_AVAILABLE_IN_CONNECTOR_EXECUTION`

## Source Lock

- Authority repository: `moeendres-png/commander-playtest-lab`
- Lab main reverified at closure: `548167fa25b8345621d4638d7c140449fa73ac31`
- Authoritative `config/rules_engines.json -> primary_engine.commit`: `db134b9737e951367d65ef5806ad986319cc73ab`
- Mage implementation repository: `moeendres-png/mage`
- Base branch containing the exact pin: `ws212/xmage-rules-rng-seed-authority-20260914`
- Base commit: `db134b9737e951367d65ef5806ad986319cc73ab`
- Base tree: `4c7cae47f355ab41739b489af383ab54bf49e908`
- Workstream branch: `sol/rg02-commander-damage-qual-20260924`
- Runtime-verified RG-02 source head: `ad2386571082a4c18b1d8528fb9ab827f7cffda5`
- Runtime-verified RG-02 tree: `3615f68655989313ee674d8b887afcbfe675b9be`
- Draft CI PR: #13. It is a CI-only vehicle and MUST NOT be merged to Mage master.

The branch is a direct descendant of the authoritative pin. No substitution with Mage `master` occurred.

## Reuse Classification

`ENGINE_NATIVE_REUSE`

The exact pinned source already contains the required native state-load seam:

`Mage/src/main/java/mage/watchers/common/CommanderInfoWatcher.java`

`restoreDamageStateForGameLoad(Map<UUID, Integer>, Game)`

The implementation validates the entire restore payload into a temporary map before mutating the native damage ledger, rejects null/unknown players and null/negative amounts, then replaces the existing native ledger. It does not synthesize historical `DAMAGED_PLAYER` events.

The existing watcher also already normalizes commander combat-damage sources through the commander's main card identity and mutate-object membership. Existing DFC commander info handling is native. The native Commander game SBA loop reads each commander's watcher independently and loses a player only when one ledger exceeds 20.

No second ledger, provider-side Rules implementation, or card-name production special case was added.

## Rules Authority Check

Current official Wizards Commander guidance was used as external Rules authority for the qualified semantics:

- 21 or more combat damage by the same commander causes loss.
- The commander is tracked across zone changes and control changes for this purpose.
- With two commanders, damage is tracked separately; damage from both is not combined.

Engine behavior was treated as evidence, not Rules authority.

## Work Completed

1. Reverified current Lab AGENTS policy, engine pin, DR-CLOSURE handoff/state/source lock, exact Mage commit existence and overlap/ownership surface.
2. Read the complete native `CommanderInfoWatcher` and Commander SBA implementation.
3. Inspected current Commander restore, mutate, MDFC, multiplayer and combat test donors.
4. Created the isolated branch from the exact project pin.
5. Added native runtime qualification tests without production Rules changes.
6. Added an RG-02-only PR checkout binding so GitHub Actions checks out the exact PR head SHA rather than a synthetic merge ref. This was necessary because the pinned engine lineage intentionally predates current Mage master.
7. Executed the repository's existing Maven workflow on the exact RG-02 source head and classified the unrelated downstream verifier failure separately.

## Production Changes

**NONE.**

No file under `Mage/src/main/java` or any production card/rules implementation was changed.

## Test / Qualification Changes

- `Mage.Tests/src/test/java/org/mage/test/serverside/rg02/RG02CommanderDamageRestoreTest.java`
- `Mage.Tests/src/test/java/org/mage/test/serverside/rg02/RG02CommanderDamageRestore4PTest.java`
- `Mage.Tests/src/test/java/org/mage/test/serverside/rg02/RG02CommanderDamageRestore5PTest.java`
- `.github/workflows/maven.yml` — branch-local exact-head checkout binding for qualification integrity.

## Required Matrix — Runtime Results

All 13 RG-02 test methods executed on exact head `ad2386571082a4c18b1d8528fb9ab827f7cffda5` and were reported `[OK]`:

1. `restore20DoesNotLoseIn3PlayerGame` — PASS
2. `restore21CausesStateBasedLossAndLaterChecksRemainStable` — PASS
3. `damageFromDifferentCommandersDoesNotAggregate` — PASS
4. `partnerCommandersHaveIndependentDamageLedgers` — PASS
5. `restored19ThenRealCommanderCombatDamageReachesThreshold` — PASS
6. `noncombatCommanderDamageDoesNotIncrementLedger` — PASS
7. `commanderDamageTracksIdentityAfterControllerChange` — PASS
8. `commanderDamageContinuesAfterBlinkReentry` — PASS
9. `modalDoubleFacedCommanderUsesFrontIdentityForDamage` — PASS
10. `mutatedPermanentNormalizesCommanderSourceIdentity` — PASS
11. `invalidRestorePayloadsFailBeforeMutation` — PASS; this one covers unknown player ID, negative amount, null amount, null player ID, null payload, null game and verifies no partial mutation.
12. `restore21CausesLossIn4PlayerCommander` — PASS
13. `restore21CausesLossIn5PlayerCommander` — PASS

This covers every required RG-02 semantic gate: 20/21 threshold, nonaggregation, independent partners, genuine later combat increment, noncombat exclusion, control change, zone leave/re-entry, MDFC source identity, mutate normalization, repeated later SBA stability, 3P/4P/5P, and invalid restore payload rejection.

## Exact Runtime / Build Evidence

GitHub Actions workflow run: `36061549925`

Job: `107841894432`

The checkout log explicitly records:

- `ref: ad2386571082a4c18b1d8528fb9ab827f7cffda5`
- fetch of exactly `ad2386571082a4c18b1d8528fb9ab827f7cffda5`
- detached HEAD exactly `ad2386571082a4c18b1d8528fb9ab827f7cffda5`
- `git log -1 --format=%H` -> `ad2386571082a4c18b1d8528fb9ab827f7cffda5`

The workflow then ran the repository command:

`mvn test -B -Dxmage.dataCollectors.printGameLogs=false -Dlog4j.configuration=file:${GITHUB_WORKSPACE}/.travis/log4j.properties`

Relevant reactor evidence:

- `Mage Framework 1.4.61` — SUCCESS
- `Mage Game Commander Free For All 1.4.61` — SUCCESS
- `Mage Server 1.4.61` — SUCCESS
- `Mage Tests 1.4.61` — SUCCESS
- Mage Tests result: `6903` run, `0` failures, `0` errors, `125` skipped.
- The three RG-02 classes appear in the executed test tree and all 13 methods are individually `[OK]`.

This is direct runtime evidence that the exact pinned lineage containing the native restore API compiled into and was exercised by the test runtime. There is no `PIN_MATERIALIZATION_MISMATCH`.

### Whole-Reactor Result

The top-level Maven reactor concluded `FAILURE` only after the successful Mage Tests module, in the independent `Mage.Verify` module:

- `VerifyCardDataTest.test_verifyCards`: 15 current card-data subtype verification errors.
- `VerifyCardDataTest.test_checkMissingSetData`: one missing set implementation (`SLZ - The Zeta Set`).

These failures are outside RG-02-owned files and do not implicate Commander damage, the restore seam, or the executed RG-02 tests. They are retained as a real ambient CI failure and are not relabeled as green CI.

## Evidence Classification

- Source pin / branch ancestry / exact checkout: `DIRECTLY_VERIFIED`
- Native implementation structure and SBA wiring: `CODE_DERIVED`
- 13 RG-02 runtime tests: `DIRECTLY_VERIFIED` + `TECHNICALLY_CONFORMANT`
- Commander-damage semantics against current official Wizards Commander rules: `EXTERNALLY_RULE_VALIDATED`
- Whole-reactor CI: `FAIL` due unrelated Mage.Verify card-data drift; not an RG-02 semantic failure.
- `PIN_MATERIALIZATION_MISMATCH`: **NOT PRESENT**

## New Findings

1. The native restore seam is sufficient for RG-02; no engine repair is required.
2. The native damage watcher correctly preserves the same commander identity through actual controller change and blink/re-entry.
3. Native mutate normalization correctly attributes combat damage when the commander card is underneath the merged permanent.
4. MDFC commander damage continues to bind to the front/card identity as expected.
5. Partner/different-commander ledgers remain independent.
6. Restore payload validation is atomic: invalid mixed payloads do not partially alter the existing ledger.
7. The repository's ordinary PR CI would otherwise build a synthetic merge ref; exact-head checkout must be bound explicitly for pin-qualified residual branches.
8. Current full Maven verification has unrelated card-data drift in `Mage.Verify`; this is not silently converted to PASS.

## PASS / FAIL / UNKNOWN

### PASS

`RG02_NATIVE_COMMANDER_DAMAGE_STATE_RESTORE = PASS`

The full required RG-02 matrix is runtime-qualified on the exact project pin lineage.

### FAIL

`FULL_MAVEN_REACTOR = FAIL_AMBIENT_MAGE_VERIFY`

The failure is outside this workstream and occurred after `Mage Tests` completed successfully.

### UNKNOWN

No required RG-02 semantic cell remains UNKNOWN.

## Production Engine Semantics Changed

`NO`

RG-02 is qualification closure with no production Rules-Core change.

## Remaining Blockers

None inside RG-02.

The ambient `Mage.Verify` card-data drift is a separate repository-maintenance concern and is not a dependency for the Commander-damage result established here.

## Dependencies Unblocked

- RG-07 may use the terminal RG-02 branch head as its exact source base.
- Subsequent residual workstreams may treat Commander-damage restore as runtime-qualified unless a later relevant production, pin, contract, or test-harness change invalidates this evidence.

## Exact Next Action

Start RG-07 from the exact terminal `RG02_MAGE_HEAD` recorded below. Do not restart from Mage master and do not merge this branch to master.
