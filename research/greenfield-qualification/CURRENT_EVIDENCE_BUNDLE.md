# Commander Simulator Next — Current WS90 Evidence Bundle

Date: 2026-08-29

This bundle is the canonical integration index for
`work/90-integration-cross-qualification-20260828`. The exact runtime tree
cross-qualified after WS01–WS10 integration is
`55820618e7243bd5ba8cfa33c3148cea8c166c73` /
`3706900d49c6ef61690c227bb7b4c0067fbcfb44`.

## Verified run / artifact inventory

| Boundary | Run / job | Artifact | Artifact SHA-256 | WS90 adjudication |
|---|---|---:|---|---|
| WS01 strict decision externalization | `33200503101` / `98948483892` | `9697626914` | `a731838e0c24ee2a25738af80aa94d59b69743b5e141a8959da3101029bf5e1f` | Q1 PASS |
| WS02 pinned Oracle corpus | `33176329547` | `9687739211` | `9dd003cc916b58aee3f7a56881b63ec0e7d2291501fa38f3d66cd285e682af4e` | corpus PASS, 38,626 indexed identities |
| WS02 official-precon source input | `33089467077` | `9653672924` | `4700fcc5c13ce0884bec3807980fcd7a310252be1a8d154edbd5c1eed498a0d0` | source input verified |
| WS05 hidden information | `33210994482` / `98983894190` | `9701653278` | `137f1978e487473266599559d5602ff7f8186cad83b327a43be380fbc3a033ab` | Q2 PASS |
| WS06 RNG / semantic replay | `33209213338` / `98977993604` | `9701086657` | `c5f80e39105abcf1d1c7bc8323394c69dc74eed4c961b687520371a7f55a8f90` | Q3 PASS |
| WS07 original Commander conformance | `33244368567` / `99079149450` | `9712369379` | `72d2f8af3ed4e9892451546132dd7e09e33400f728983f6f0e9be341540b2c5e` | original Q5 PASS; superseded for integrated-stack proof by WS90 rerun |
| WS08 process isolation | `33211580138` / `98985813266` | `9701960978` | `29c16cae97c83b46246fcd0e3ac27da00a979f8c0f062d070087b09327555f19` | Q4 PASS, process-per-game |
| WS09 differential | `33246123537` / `99083770804` | `9712936171` | `44b106695591afb1853d7d11273466c093c95fb7f67aabdce9df3937fe6501ff` | Q7 PASS, two-scenario scope |
| WS10 card coverage claim | `33247342048` / `99086999845` | `9713305048` | `b4e494b93500749dc4eb50e25793e682069661980b5e9331db500c4c6ac1d0f0` | evidence retained; Q6 PASS claim rejected |
| WS90 integrated Q5 / Q7 Forge side | `33250119165` / `99094251297` | `9714119110` | `d5bdb8b59045c78c5c3774bac1f9091c7b32327834eea9abf106412452cdcb4c` | integrated Q5 PASS; 3P player-count/life facts PASS |

All downloaded WS01/WS05/WS06/WS07/WS08/WS10/WS90 ZIP digests were
independently recomputed and matched GitHub's artifact digests. Internal
`hashes.sha256` manifests were also checked where supplied.

## Machine-readable gate facts

- Q1: 4P game completed, 699/699 responses accepted; production-reachable
  untyped decisions = 0; production-reachable fallback decisions = 0.
- Q2: pilot-visible hidden-information leaks = 0; cross-principal decision
  leaks = 0 across the required 4P campaign surfaces.
- Q3: three fresh processes; semantic-state/RNG-event/decision-event
  divergences = 0.
- Q4: process-per-game PASS; cross-game controller, queue, observation, RNG and
  state leaks = 0; one worker failure did not corrupt the other game.
- Q5 integrated: 42/42 authoritative semantic rows, A–T 20/20, C01–C22 22/22,
  mandatory 4P scenarios and 2P–5P subsets PASS.
- Q7: official-rules adjudicated two-scenario Forge/XMage comparison; WS90
  freshly requalified the changed Forge side.
- Q6: WS10 produced 0 `FULL`, 1,678 `CONDITIONAL_FULL`, 0 PARTIAL/UNKNOWN/
  UNSUPPORTED, but WS90 rejects that as behavioral closure because the
  decision/hidden/replay flags are inherited from global workstream PASS values
  rather than actual per-identity semantic execution.
- Q8: WS03 license inventory/boundary subgate is complete, while final Q8 is
  explicitly deferred pending a concrete architecture/distribution topology.
- Failure semantics: incomplete as an integrated taxonomy.

## Source / handoff inventory

Exact workstream heads and trees, ownership adjudication, modified/rejected
claims, rerun classifications and blockers are recorded in
`WS90_INTEGRATION_ADJUDICATION.json`. `CURRENT_STATUS.md` is the human-readable
canonical status and `NEXT_HANDOFF.md` defines the next dependency wave.

This evidence bundle does **not** support Architecture Freeze or production
repository creation.
