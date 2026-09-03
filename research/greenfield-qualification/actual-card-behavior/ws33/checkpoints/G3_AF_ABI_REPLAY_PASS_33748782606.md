# WS33 G3 AF ABI / RNG / Replay — immutable PASS checkpoint

Status: `PASS`

This checkpoint closes the non-hidden evidence obligations for the 21 AbilityFactory-compatible G SVar paths. It does not mutate WS33 coverage and it does not yet promote the AF paths; Principal Observation / hidden-information qualification remains separate.

## Exact evidence identity

- branch: `work/ws33-g3-final-closure-20260902`
- workflow source HEAD: `b599cb1550c3e04f099eb59dd4aae1e117078167`
- workflow source TREE: `9944a7f8295222839f4efef92be562c84ebc09ef`
- run: `33748782606`
- job: `100627296583`
- artifact: `9890829899`
- artifact digest: `sha256:77fe10f72233e824169829a2e7526103cb0bacf8b06823379ce57f44472359eb`
- downloaded ZIP SHA256: `77fe10f72233e824169829a2e7526103cb0bacf8b06823379ce57f44472359eb`

Immutable AF behavior dependency:
- behavior HEAD: `28f4e7cdd6a35c488d4633cf8d77163a8aa2d5d9`
- behavior TREE: `fa5cb7385b2724433cf877b11e890985adef2376`
- behavior artifact: `9889684290`
- behavior digest: `sha256:7a9b8a4e8dd993d419d55fa31763ef8d49ffc3927408bfdb4488724dd16d68e9`

Runtime source split used to reconstruct the exact green behavior boundary:
- retained Direct-G runtime source HEAD `d8af15cb879bdfc3c40ce4cba3462da24ee3f272`
- retained Direct-G runtime source TREE `857dc01e04f58ca59437e08710bcb194bf030ea4`
- AF tooling source HEAD/TREE exactly equal to the immutable AF behavior dependency above.

Other exact pins:
- Forge `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- model artifact `9823383539`
- effective model SHA256 `cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224`
- WS01 `bf089ea806f54a9bbb64ede205915729e3629684`
- WS12 `80743bdbc2950b00e422f3deb38f04111f30a4d4`
- WS32 `6ca2a7bbacd074cc84fa4a6019c4d26e5e3717a9`
- historical WS31 harness infrastructure `b09fe7c16845cddbbfe30fd1f855b59234bbf007`.

## Machine adjudication

`WS33_G_ABI_REQUEST_EVIDENCE.json`:
- schema `commander-simulator-next.ws33-g-abi-request-evidence.v2`
- status `PASS`
- path count `21`
- Decision-required `9`; observed `9`
- RNG-required `4`; observed `4`
- request event count `47`
- Record/Replay request trace equal `true`
- request identity scope `principal_id+token`
- authoritative legal options captured from request `true`
- request envelope cross-checked: decision_id, decision_kind, actor_id, principal_id, token
- hidden identity payload retained `false`
- minimum requirement semantics `true`
- silent fallback `false`
- coverage mutated `false`.

Source-proven Replay-required AF paths: `12`.

## Record / Replay equality

The following retained files are byte-identical between Record and tape-driven Replay:

- `case-summary.tsv`
- `decision-tape.tsv`
- `decision-events-with-path.tsv`
- `rng-tape.tsv`
- `rng-events-with-path.tsv`
- `decision-requests-with-path.tsv`

The Record campaign itself is 21/21 PASS, 21/21 stack admission/resolution, 21/21 target-SVar reachability, and is byte-identical to the immutable AF behavior Record.

The isolated target-selection regression is PASS.

## Closure classification

`TECHNICALLY_CONFORMANT` for the AF Decision/RNG/Replay evidence obligations against the exact immutable behavior/runtime/model pins above.

This closes the source-pin defect diagnosed in runs `33746404465` and `33747841460` without weakening principal observation, legality, decision validation, target binding, or failure semantics.

## Remaining AF blocker

Principal Observation / hidden-information evidence is still required for `19/21` AF paths. No AF promotion may occur until that separate gate passes with strict principal-scoped observation lifecycle and Record/Replay evidence.

`WS33_COMPLETE = FALSE`
