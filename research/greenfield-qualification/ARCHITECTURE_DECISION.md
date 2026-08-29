# Architecture Decision — WS90 Current State

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`  
`READY_FOR_GREENFIELD_BUILD = FALSE`

The completed WS90 integration makes Forge at
`8c7e9afb8e6caee88644b94e25da5852e36f8928` the strongest current Rules-Core
hypothesis, but not a selected production architecture.

## Qualified facts

- Q1 strict external decisions: PASS; production-reachable untyped and fallback
  decisions are both zero in the qualified 4P run.
- Q2 hidden information: PASS; pilot-visible leaks and cross-principal decision
  leaks are zero in the qualified 4P campaign.
- Q3 RNG/replay: PASS; three fresh processes reproduce state, RNG and decision
  streams with zero divergence.
- Q4 isolation: PASS under **process-per-game**. Same-JVM multi-game isolation is
  not qualified.
- Q5 Commander/multiplayer: PASS on the integrated WS01+WS05+WS06 Forge stack;
  A–T 20/20, C01–C22 22/22, mandatory 4P and 2P–5P subsets pass.
- Q7 differential: PASS only for the two selected Forge/XMage common-state
  scenarios; phase.rs and Manabrew remain unsupported/unknown for that adapter.

Exact integrated runtime proof: `55820618e7243bd5ba8cfa33c3148cea8c166c73`
/ `3706900d49c6ef61690c227bb7b4c0067fbcfb44`, run `33250119165`, artifact
`9714119110`.

## Freeze blockers

```text
Q6_ACTUAL_CARD_BEHAVIOR = FAIL
FAILURE_SEMANTICS       = FAIL_INCOMPLETE
Q8_LICENSE_THIRD_PARTY  = DEFERRED_PENDING_ARCHITECTURE_SELECTION
```

WS10's 1,678-card load/construct census is retained, but its Q6 PASS conclusion
is rejected because card-level decision/hidden/replay PASS is inherited from
global workstream gates and dedicated behavior proof is triggered only by hard
source warning markers. This does not establish actual per-identity rules
behavior.

WS03's license inventory is complete as a subgate, but its architecture-
dependent final license decision is explicitly unfinished.

See `WS90_INTEGRATION_ADJUDICATION.json`, `CURRENT_STATUS.md` and
`NEXT_HANDOFF.md` for exact workstream heads, artifacts, modified claims and the
next dependency wave. Do not create `moeendres-png/commander-simulator-next`
from this state.
