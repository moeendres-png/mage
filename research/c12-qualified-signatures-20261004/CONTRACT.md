# Qualified signature repair (review P1, Mage43)

Contract successor baseline/policy4, direct execution3, aggregate witness5.
Before: source363b70afdc3eca17d4ef8f4883da02ff5a4ad37d credited both
unchanged proof(one.Foo) and replacement proof(two.Foo), using the real full
pipeline. These are distinct declarations; name-only erasure is insufficient.
After: primitives and explicitly qualified reference spellings only; witness
Class.getTypeName() preserves actual qualified names and array shape. No import,
bound or nested resolution guessed. Unsupported parameters fail closed. All
6835 enabled native Mage baseline methods have no parameters, so this restriction
does not drop any current native obligation. New parameterized tests must use
supported explicit spellings or receive a separately reviewed resolver change.

The old v3 controls/source locks remain historical; they do not qualify this
successor. This repairs method identity; no hostile same-JVM containment claim.
Counter fixture is regenerated through the full pipeline, not upgraded JSON.

Validation: full controls79/79 PASS,0notrun, counter contracts10/10 PASS.
Before counter suite on363b70af had84 failing assertions because the old witness
schema3 was rejected asUNKNOWN. The current positive witness is now produced by
an actual full pipeline; historical epochs are preserved and refused explicitly.
Full controls and source hashes are retained here. Standard reproduction uses
.github/qualification/qualification_selftest.py --maven /usr/bin/mvn --offline
--sandbox-user nobody --out REPORT after providing a Maven seed and pinned JUnit
standalone1.9.3. The committed wrapper documents this local cache/path mapping.
Exact-head hosted controls and independent review remain before merge.
