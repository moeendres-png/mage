# Final Engine Scorecard — Current Qualification State

Date: 2026-08-28

This is a fail-closed scorecard. It is not a production architecture freeze.

| Candidate | Rules evidence | Decision boundary | Hidden info | RNG/replay | Isolation | Actual cards | Current result |
|---|---|---|---|---|---|---|---|
| Forge `8c7e9afb...` | strongest broad 2P–5P / Commander evidence retained | new Player/Card/entity seam static+compile PASS; full 109/15 census FAIL | historical raw leak 74; principal runtime NOT_RUN | contracts present; runtime tapes NOT_RUN | no selected production core | Scryfall upstream PASS; requirement union 0/1,721 NOT_RUN | strongest Rules Core hypothesis; not admissible |
| XMage `86d86b58...` | targeted Commander evidence retained | complete external-pilot runtime gate false | principal-scoped observation gate false | incomplete | incomplete | behavior closure absent | differential/reference candidate |
| phase.rs `fae406c...` | typed targeted conformance retained | source-externalizable, all required decisions not externalized/tested | useful visibility evidence, not final pilot proof | incomplete | incomplete | major unimplemented surface | reference candidate |
| Manabrew `754ec2ae...` | headless/parity/isolation evidence retained | exact-pin first/default/pass/random fallback audit FAIL | incomplete | internal random target not explicit tape | historical 4P two-game PASS | not closed | reference only |

## Gate summary

```text
Q0 provenance/schemas       PASS locally
Q1 decisions               FAIL
Q2 hidden information      FAIL / not proven
Q3 RNG and replay          NOT_RUN
Q4 process isolation       INSUFFICIENT_EVIDENCE
Q5 Commander matrices      INCOMPLETE
Q6 actual-card coverage    INSUFFICIENT_EVIDENCE
Q7 differential            INCOMPLETE
Q8 license boundary        DEFERRED
```

The exact current blocker is
`DECISION_EXTERNALIZATION -> FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE`.
The patch directly routes only `chooseCardsForEffect`,
`chooseSingleEntityForEffect`, and `chooseEntitiesForEffect`; 106 controller
declarations remain outside the typed runtime boundary.

## Verdict

No candidate satisfies all mandatory gates. Forge Rules Core is not rejected,
but the research patch is not a production implementation. Keep
`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE` and do not create the production
repository.
