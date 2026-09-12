# WS81 Final Report — XMage Corrected H01 Engine-Direct Requalification

## Verdicts

- SOURCE_LOCK = PASS (7135d5e85ddb4c8aa4b49b4192ca51947c822704 / ea193e0d04493d53d962ed13ebd3b5d2f68838c7)
- AUTHORITY_LOCK = PASS (CPL ee4d6297; cases sha256 03390ede…; adjudication sha256 e9c35a89…)
- ACTUAL_CARDS = PASS (Clone, Humility, Runeclaw Bear — real implementations)
- XMAGE_H01_A_HUMILITY_FIRST = FAIL
- XMAGE_H01_B_CLONE_FIRST = PASS
- XMAGE_H01_C_NO_HUMILITY = PASS
- XMAGE_H01_CORRECTED_REQUALIFICATION = FAIL
- PRODUCTION_ENGINE_FILES_CHANGED = NO
- HISTORICAL_PASS_IMPORTED = NO
- FIRST_WAVE_CURRENT_RANKING = INVALID_PENDING_COORDINATOR_ADJUDICATION
- BEHAVIOR_CREDIT_CHANGE = 0
- FULL107_BEHAVIOR = NOT_RUN
- ARCHITECTURE_FREEZE = NOT_CLAIMED
- PRODUCTION_PROVIDER = NOT_SELECTED

## What was done

1. Verified source lock (branch, HEAD, tree) against the accepted pin.
2. Obtained the binding WS79 authority read-only from local CPL
   (`git fetch origin ee4d6297...`, `git show FETCH_HEAD:...`) and hashed both files.
3. Inspected the accepted-pin implementations: Clone (EntersBattlefieldAbility +
   CopyPermanentEffect), Humility (layers 6/7b), Runeclaw Bear (vanilla 2/2),
   plus EntersBattlefieldEffect / CopyEffect / TestPlayer strict-mode seams.
4. Implemented one dedicated test class, test-only:
   `Mage.Tests/src/test/java/org/mage/test/serverside/ws81/WS81H01CorrectedTest.java`
   with exactly three cases (A/B/C), strict choose mode as the
   decision-occurrence discriminator, mid-game runCode/checkPT probes for the
   under-Humility state, and Disenchant-based Humility removal for the
   post-Humility discriminator (no Clone rewrite, no production touch).
5. Executed fresh runtime:
   - `mvn -pl Mage.Tests test -Dtest=WS81H01CorrectedTest -DfailIfNoTests=false`
     => 3 run, 1 failure (A red, B/C green).
   - Regressions `mvn -pl Mage.Tests test -Dtest='CloneTest,HumilityTest'`
     => CloneTest 7/7, HumilityTest 1/1, all green.
6. Preserved evidence (this package + surefire reports) and stopped without
   production remediation per the requalification-only boundary.

## New findings (fresh DIRECTLY_VERIFIED runtime)

- H01-A is an engine defect (ENGINE_DEFECT, preserved red): with Humility
  pre-existing on the battlefield, casting Clone still prompts
  "Use effect of Clone? Yes/No" (chooseUse), i.e. the engine offers the copy
  decision the corrected authority forbids. Strict-mode failure:
  `Missing CHOICE def for turn 1, step PRECOMBAT_MAIN, PlayerA`
  at `EntersBattlefieldEffect.replaceEvent(EntersBattlefieldEffect.java:101)`
  via `TestPlayer.chooseUse(TestPlayer.java:2745)`.
- H01-B and H01-C conform: copy decisions occur and are consumed, Bear-copy
  identity is established, Humility makes it 1/1, and after Humility leaves
  the permanent remains the 2/2 Bear copy (B) / normal 2/2 copy (C).
- CODE_DERIVED root-cause location (no production edit made): the Clone entry
  path never applies CR 614.12 — `EntersBattlefieldEffect.replaceEvent`
  offers optional use unconditionally, and `CopyPermanentEffect.apply`
  offers the copy target unconditionally, without considering pre-existing
  continuous effects that would remove Clone's own copy ability.

## Per-case results

- A HUMILITY_FIRST = FAIL (offered copy decision contradicts authority;
  post-Humility 0/0->SBA assertions encoded but unreachable past the prompt).
- B CLONE_FIRST = PASS (decision consumed, 2/2 pre-Humility, 1/1 under
  Humility, 2/2 Bear copy retained after Humility leaves).
- C NO_HUMILITY = PASS (decision consumed, normal 2/2 Bear copy).

## Tests / evidence

- New: WS81H01CorrectedTest (3 tests). Fresh counts above.
- Surefire: `Mage.Tests/target/surefire-reports/TEST-org.mage.test.serverside.ws81.WS81H01CorrectedTest.xml`
  (3 tests, 1 failure, stack trace preserved).
- Regressions: CloneTest 7/7, HumilityTest 1/1 green (harness unchanged).
- Authority hashes in AUTHORITY_LOCK.json; results in H01_RESULTS.json.
- Env: Maven 3.9.12, Java 21.0.12 Ubuntu, linux wsl2 amd64.

## Remaining blockers

- H01-A engine defect requires a separate bounded remediation workstream
  (production fix OUT OF SCOPE here). No remediation attempted.

## Dependencies unblocked

- Coordinator adjudication can consume: per-case PASS/FAIL, preserved red
  evidence, CODE_DERIVED scope, terminal FAIL verdict.

## Exact Next Action

- Bounded remediation workstream: implement CR 614.12 applicability on the
  entering-copy path (consider pre-existing continuous effects before offering
  Clone's self copy replacement), re-run WS81 family expecting A/B/C green,
  without touching First-Wave aggregates or claiming broader credit.
