# AF8 run 34217074471: adjudication-contract diagnosis

```
CURRENT_FAILURE_CLASS = QUALIFICATION_EVIDENCE_CONTRACT_MISMATCH
CURRENT_FAILING_CASE = forge-behavior-v2:9c210fe6f626c37c9b3bdd9134a4bfc26dc74fd4
CURRENT_FAILING_PATH = forge-behavior-v2:9c210fe6f626c37c9b3bdd9134a4bfc26dc74fd4
CURRENT_FAILING_INVARIANT = stale byte equality of AF8_CLIENT_OBSERVATION_SAMPLES.tsv
PRODUCER_OR_ADJUDICATOR = workflow expectation; adjudicator evidence contract is correct
ROOT_CAUSE_CLASS = Case A: adjudication/test expectation defect
P_CLASS = P2
MINIMAL_OWNED_FILES = workflow plus focused regression
```

Directly verified sealed evidence shows every AF8 semantic gate as `PASS`, including
strict decision-path parity, effect evidence, principal-scoped normalized transient
observations, and each run's real-client visibility checks.  Record and replay differ
only in an aggregate transport sample count (`1` versus `2`) for one real remote
principal; both counts meet the adjudicator's intentional `>=1` contract and both have
zero visibility mismatch.  Aggregate asynchronous sample multiplicity is not a
semantic replay artifact.  No runtime producer, Forge Rules Core, decision validator,
or coverage registry is changed.
