# Engine Scorecard — WS90 Integrated Qualification

Date: 2026-08-29

This scorecard is canonical for the current integration result. The word
`FINAL` in the filename does not imply Architecture Freeze.

| Candidate | Rules / Commander | External decisions | Hidden info | RNG / replay | Isolation | Actual-card behavior | License / role | WS90 result |
|---|---|---|---|---|---|---|---|---|
| Forge `8c7e9afb…` | **PASS** for WS07 A–T 20/20, C01–C22 22/22, mandatory 4P and 2P–5P subsets; requalified on integrated WS01+WS05+WS06 stack | **PASS**; 699/699 4P decisions accepted; 109/15 census complete; untyped/fallback = 0 | **PASS**; required 4P principal surfaces, leaks = 0 | **PASS**; fresh A/B/C, zero semantic/RNG/decision divergence | **PASS process-per-game**; same-JVM multi-game not qualified | **FAIL for Q6**; 1,678 loadable/constructable identities but WS10's behavioral closure criterion is insufficient; 0 direct semantic FULL identities | GPL-3.0; exact production topology not yet license-adjudicated | strongest Rules Core hypothesis; **not freeze-admissible yet** |
| XMage `86d86b58…` | exact-pin shared 3P facts agree with official rules and Forge in WS09 | production external-pilot boundary not qualified | principal pilot boundary not qualified | not qualified to WS06 standard | not qualified | corpus behavior closure not qualified | MIT | reference engine for differential adjudication |
| phase.rs `fae406c…` | useful typed/reference implementation evidence retained | partial/source-level evidence only | incomplete for production boundary | incomplete | incomplete | major coverage gaps / no WS10-equivalent closure | MIT OR Apache-2.0 | reference only; WS09 constructed-state adapter unsupported |
| Manabrew `754ec2ae…` | historical/reference evidence retained | prior fallback concerns remain disqualifying for production pilot boundary | incomplete | not qualified to explicit game-scoped tape standard | historical evidence does not replace current selected-candidate Q4 | no current behavior closure | AGPL-3.0-or-later; embedded Forge gitlink GPL-3.0 | reference only; WS09 adapter unsupported |

## Mandatory gate matrix

```text
Q0 provenance/schemas       PASS
Q1 decisions                PASS
Q2 hidden information       PASS
Q3 RNG / semantic replay    PASS
Q4 process isolation        PASS_PROCESS_PER_GAME
Q5 Commander / multiplayer  PASS
Q6 actual-card behavior     FAIL
Q7 differential             PASS_SCOPE_LIMITED
Q8 license boundary         DEFERRED_PENDING_ARCHITECTURE_SELECTION
Failure semantics           FAIL_INCOMPLETE
```

## What changed in WS90

- Historical Q1/Q2/Q3/Q4/Q5 failure/incomplete claims are superseded by exact
  current workstream artifacts and, for Q5, a fresh integrated rerun.
- WS08 demonstrates the dependency stack WS01+WS05+WS06+WS08 compiles and is
  isolated under a process-per-game model.
- WS90 run `33250119165` demonstrates WS07 semantics still pass after the
  integrated WS01+WS05+WS06 Forge changes.
- WS10's green workflow is not accepted as Q6 behavioral proof. Its classifier
  promotes card flags from global dependency PASS values; absence of source
  warning markers is treated as absence of dedicated behavior requirements.
  That is weaker than actual-card semantic execution.
- WS03's license inventory is accepted, but Q8 remains explicitly deferred.

No candidate currently satisfies all mandatory freeze gates. Forge remains the
best technical hypothesis, not a frozen production Rules Core.
