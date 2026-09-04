# WS33 G3 non-AF ABI / Decision / RNG / Replay Certification — PASS

STATUS = PASS
EVIDENCE_CLASS = DIRECTLY_VERIFIED

Certification source:
- HEAD = ac4c6b9fba8e809a42e3e4d9f37c3f00178f6820
- TREE = 13d7c0c34fbd39361aeff5c59b919ba8a595d602
- exact-source run cardinality = 1

GitHub Actions:
- RUN = 33929080030
- JOB = 101203805362
- WORKFLOW = .github/workflows/ws33-g3-svar-event-abi-replay-certify.yml
- CONCLUSION = success
- ARTIFACT_ID = 9957878386
- ARTIFACT_NAME = ws33-g3-svar-event-abi-replay-certification-33929080030
- GITHUB_DIGEST = sha256:d26c61446bf023af1f26ba6d9ef7f94e843e7726915c6b47578f8226662793da
- INDEPENDENT_ZIP_SHA256 = d26c61446bf023af1f26ba6d9ef7f94e843e7726915c6b47578f8226662793da

Consumed immutable runtime:
- RUNTIME_HEAD = 2896cca14dcc0d43a92957b3ddb4e8e11f1f28c7
- RUNTIME_TREE = fbb9565d4583db655872cfd378831711b0989b7a
- RUNTIME_RUN = 33928315020
- RUNTIME_JOB = 101201530278
- RUNTIME_ARTIFACT = 9957712911
- RUNTIME_DIGEST = sha256:2241adad950188fc0f0adb0d0a1395a399251470dc8d8e75ded96d68d61aea0b

Directly verified gates:
- artifact ZIP independently re-hashed and equals GitHub digest
- certification SHA256SUMS independently verified after extraction
- runtime artifact digest/source/pin/model/topology chain verified
- frozen Record/Replay identity PASS
- effective paths = 32
- source parents = 33
- hidden-required paths = 31
- Decision-required = 22/22 observed
- RNG-required = 10/10 observed
- ABI adjudicator regressions = 10/10 tests PASS
- authoritative legal options captured from request = true
- request identity = principal_id + token
- hidden identity payload retained = false
- silent fallback = false
- coverage_mutated = false
- principal_observation_promoted = false

G3.4 = PASS.

NEXT_ACTION = implement/run the separate G3.5 principal-observation certification for exactly the 31 hidden-required non-AF effective paths, consuming the frozen runtime/certification lineage. Do not promote G coverage before G3.5 passes.
