# C12 method identity P1 follow-up

Owned branch: hardening/c12-method-identity-20261004; parent Lab#493/#479.
The source and raw full-path before/after controls are in this directory. Before
fixture bundles contain the original exact candidate roots and complete histories;
`git bundle verify` succeeded. Their hashes and candidate roots are in the lock.

Commands: `python3 .github/qualification/corpus_policy.py generate --repo . --rev HEAD
--out .github/qualification/test_corpus_baseline.json`; full production-control suite
via the committed run-c12-identity-controls-20261004.py as root with trusted PATH
/usr/bin:/bin. The wrapper only selects the recorded local cache/sandbox/output
paths; change those paths for a fresh host/run, never reuse an occupied fixture root.
For hosted use the unchanged candidate-qualification-selftest workflow.

75/75 controls, zero NOT_RUN. Nested removal/disable and overloaded deletion FAIL;
unchanged nested/overloaded declarations PASS. Ambiguous signatures are explicitly
refused. Baseline remains1997 classes/6835 enabled/140 disabled, with no approvals.
Only qualification contracts/harness changed, no Rules engine or candidate pin.

Next: push, exact-head hosted controls, adversarial review, explicit schema-bootstrap
impact adjudication before merge; native Verify drift remains a separate C13/C14
issue. A green self-test does not establish same-JVM adversarial containment or full
Mage corpus runtime. Do not close C12 merely because this P1 is repaired.
