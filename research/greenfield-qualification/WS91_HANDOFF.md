# WS91 — Post-WS11/WS12 Cross-Qualification & Topology Adjudication — Handoff

`WORKSTREAM_COMPLETE = TRUE`

`WS13_ELIGIBLE = FALSE`

`INITIAL_ARCHITECTURE_DECISION_FROZEN = FALSE`

`READY_FOR_GREENFIELD_BUILD = FALSE`

## Provenance

- Repository: `moeendres-png/mage`
- Branch: `work/91-semantic-failure-cross-qualification-20260829`
- Required base / WS90 final canonical integration HEAD: `624c0a652de775dcdf9d641438b5c18ef4ce50d2`
- Base tree: `f47e41f0fc09349579f480acd0ca2593c7aceca1`
- Retained qualified runtime HEAD/tree: `55820618e7243bd5ba8cfa33c3148cea8c166c73` / `3706900d49c6ef61690c227bb7b4c0067fbcfb44`
- Exact Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- Adjudicated status HEAD/tree before this documentation-only handoff commit: `e6233888f468c0e740dbcd8621e5e491dd240067` / `0b31cae3e151b1ac9ff230f99b9eb75edd2c902b`
- `FINAL_HANDOFF_HEAD = SELF`; report the resulting branch tip externally after creation.

## What WS91 independently verified

WS91 did not trust workstream COMPLETE claims. It independently checked the live branch tips, ancestry and changed-file ownership for WS14–WS25 and directly checked the relevant GitHub Actions job/artifact metadata.

### Q6 chain

- WS14 final: `d8c1ee0c08c7e7f0bc2bc86c70166ebc198e30d5`
- WS15 final: `93abc135fe5029781335b4c026736a191451af78`
- WS16 final: `2ec85801ce0f2c9fa66c0d8c61f56f5c08b8ca0e`
- WS17 final: `a5f68f9ec49d19d900e92e505654871d2267ba93`
- WS18 final: `5f575e43aed11d0bf0eb0dceac9ed7f258370d31`
- WS19 final: `61f345603b39aa555d4682fea40f7cc29a598073`
- WS24 final: `7267a6ead4fbc7c72a0d0e2e8da1c0e5ca8e34e6`

WS15–WS19 all have the exact WS14 final HEAD as merge base and change only their own witness-shard/workflow/handoff ownership. WS24 has the exact WS90 base as merge base and integrates the WS14 model plus the five immutable shard artifacts read-only.

The WS24 qualification was directly verified:

- tested HEAD/tree: `5b7dc610caadaa3d9539e26bca3bda5879955fe0` / `6647325ed48bcadb8439812006d9fa6ca4093e67`
- run/job: `33273280712` / `99155505569` — SUCCESS
- artifact ID: `9720751546`
- artifact digest: `sha256:512c4d9f1fdae11aab8bb6145af2df02e3d2c42205ac42c17d521fcd34e267b9`
- internal artifact hashes: independently verified

Its machine gate states:

```text
identity_count              = 1678
primitive_count             = 174
primitive_pass              = 13
primitive_partial           = 161
unproved_primitive_count    = 161
unresolved_binding_count    = 1800
identity_partial            = 664
identity_unknown            = 1014
Q6_ACTUAL_CARD_BEHAVIOR     = FAIL_CLOSED
q6_pass                     = false
```

The 13 PASS primitives were independently traced to WS16 (`2`) and WS17 (`11`). The exact PASS witness artifacts use Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`, have `execution=PASS`, `stdout_only=false`, state evidence, and immutable trace hashes.

WS16's first job `33270636779` / `99148367194` is correctly treated as two-stage evidence: the pinned-Forge execution and artifact upload succeeded before a later artifact-identity packaging step failed. The separate recovery run `33272938913` / `99154590943` successfully re-downloaded, provenance-checked, hashed and WS14-ABI-materialized that immutable execution artifact. No engine execution was invented or inferred from the later recovery.

### Failure-semantics chain

- WS20 final: `df146cd5aa404c2c371bc1591416d4bf57dbf2cc`
- WS21 final: `a016ac70778c0784857f5e3247629e5866a16e15`
- WS22 final: `45f5691ab4cc1e8a2e4a0904b041ef08a1613612`
- WS23 final: `b773d490f2e5610a72499f8633ef3e3b82be3757`
- WS25 final: `f40e12bc321223ec1a4918fa3f0e425ec5651ba2`

WS20–WS22 descend from exact WS12 base `80743bdbc2950b00e422f3deb38f04111f30a4d4` and stay within their adapter/workflow ownership. WS23 intentionally descends from WS14, with the WS12 outcome contract and WS17 witness artifact consumed read-only; its changed files remain confined to the card-behavior qualifier adapter/workflow/handoff. WS25 descends from the exact WS90 base and integrates the four successor evidence artifacts read-only.

WS91 directly verified the WS20–WS23 job/artifact identities and digests claimed by WS25. WS25 itself was directly verified:

- tested HEAD/tree: `05cf89a5ef515f84fc81ddd4db9aba788704df06` / `bac6cc5600c20b879e0d826959a728d1b7245777`
- run/job: `33275091071` / `99160294360` — SUCCESS
- artifact ID: `9721261751`
- artifact digest: `sha256:2e1bc7c04eafecf211b6647fb97ce490c09cfca250c038dd35f22e54ecb641cf`
- internal artifact hashes: independently verified

The WS25 machine gate accounts for all `16` authoritative categories. Exactly one production-reachable category remains unbound:

`CARD_BEHAVIOR_FAILURE`

WS23 proves a controlled semantic mismatch detector only as `QUALIFIER_ONLY` and explicitly establishes no production runtime callsite. Therefore:

```text
production_reachable_untyped_failure_outcomes = 1
production_reachable_fallback_observed_count   = 0
production fallback absence on unbound path    = UNKNOWN
FAILURE_SEMANTICS                              = FAIL_CLOSED
```

## Re-adjudication Q0–Q8 + failure semantics

| Gate | WS91 adjudication |
|---|---|
| Q0 | `PASS` |
| Q1 | `PASS — NO_RERUN` |
| Q2 | `PASS — NO_RERUN` |
| Q3 | `PASS — NO_RERUN` |
| Q4 | `PASS — PROCESS_PER_GAME — NO_RERUN` |
| Q5 | `PASS — NO_RERUN` |
| Q6 | `FAIL_CLOSED` |
| Q7 | `PASS — SCOPE_LIMITED — NO_RERUN` |
| Q8 | `DEFERRED` |
| FAILURE_SEMANTICS | `FAIL_CLOSED` |

No predecessor runtime qualification was rerun because the integrated successor changes do not replace the WS90 qualified runtime source or modify the retained Q1–Q5/Q7 runtime contracts. Re-running them solely for reassurance would not create new evidence.

## Mandatory topology question

WS91's mandatory conjunction fails:

```text
Q6_ACTUAL_CARD_BEHAVIOR = PASS      -> FALSE
FAILURE_SEMANTICS = PASS            -> FALSE
same compatible candidate topology  -> NOT ESTABLISHED
WS13_ELIGIBLE                        -> FALSE
```

Consequently WS91 does **not** issue a license-ready architecture candidate and does not attempt architecture freeze. The technically proven constraints that remain valid are recorded separately in `WS91_TOPOLOGY_HANDOFF.md`, but unresolved packaging/IPC/modification/distribution choices are deliberately not frozen or sent to WS13 as an eligible topology.

## Exact blockers / next evidence

### Q6

`161` of `174` atomic primitives remain non-PASS and `1800` WS14 source bindings remain unresolved. Close them systemically with actual exact-pinned Forge execution, authoritative legal decisions, state assertions, immutable trace hashes and decision/RNG tapes where relevant. No card-name production hacks, source-presence promotion, or global Q2/Q3 inheritance may substitute for actual behavior proof.

### Failure semantics

Bind `CARD_BEHAVIOR_FAILURE` to a real production-runtime semantic-verifier/capture path. Induce an actual mismatch there, emit the authoritative typed outcome, and prove no failed-state commit, no fallback coercion, and no private-data disclosure.

Only the successor integration gates whose inputs change should then be rerun. Other predecessor gates remain untouched unless a concrete implementation change invalidates them.

## Canonical files emitted/updated by WS91

- `research/greenfield-qualification/WS91_CROSS_QUALIFICATION.json`
- `research/greenfield-qualification/WS91_TOPOLOGY_HANDOFF.md`
- `research/greenfield-qualification/WS91_HANDOFF.md`
- `research/greenfield-qualification/CURRENT_STATUS.md`
- `research/greenfield-qualification/NEXT_HANDOFF.md`

No production repository was created. No architecture decision was frozen. No Q8 claim was made.
