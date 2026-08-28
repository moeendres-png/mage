# Final Engine Scorecard — Current Qualification State

Date: 2026-08-28

This is a fail-closed scorecard at research revision `5897a196…`. It is not a
production architecture freeze.

| Candidate | Rules evidence | Decision boundary | Hidden info | RNG/replay | Isolation | Actual cards | Current result |
|---|---|---|---|---|---|---|---|
| Forge `8c7e9afb…` | current CLI probes 2P–5P return PASS; 4P is primary target | Java validator and metadata-only Decision-Tape PASS; static 109/109 and 15/15 census complete, but 106 paths lack full runtime externalization | current scoped 2P decoded transport is 0 names; all other required surfaces unqualified | three fresh processes have no semantic state/RNG/full-game decision streams | no selected production-core isolation proof | upstream Scryfall 38,626; project union 0/1,721 | strongest Rules Core hypothesis; not admissible |
| XMage `86d86b58…` | targeted Commander evidence retained | complete external-pilot runtime gate false | principal-scoped observation gate false | incomplete | incomplete | behavior closure absent | differential/reference candidate |
| phase.rs `fae406c…` | typed targeted conformance retained | source-externalizable, full decision surface unqualified | useful visibility evidence, not final pilot proof | incomplete | incomplete | major unimplemented surface | reference candidate |
| Manabrew `754ec2ae…` | headless/parity/isolation evidence retained | exact-pin first/default/pass/random fallback audit FAIL | incomplete | internal random target not explicit tape | historical 4P two-game evidence only | not closed | reference only |

## Gate summary

```text
Q0 provenance/schemas       PASS locally
Q1 decisions                FAIL (static census complete; 106 runtime paths)
Q2 hidden information       scoped raw transport PASS; overall insufficient
Q3 RNG and replay           NOT_RUN
Q4 process isolation        INSUFFICIENT EVIDENCE
Q5 Commander matrices       INCOMPLETE
Q6 actual-card coverage     INSUFFICIENT EVIDENCE
Q7 differential             INCOMPLETE
Q8 license boundary         DEFERRED
```

The exact first blocker is:

```text
DECISION_EXTERNALIZATION -> FULL_DECISION_CENSUS_AND_TYPED_CALLBACK_COVERAGE
```

No candidate satisfies Q0–Q8. Keep
`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`; do not create the production
repository. Current remote evidence is indexed in
`REMOTE_QUALIFICATION_EVIDENCE.json`.
