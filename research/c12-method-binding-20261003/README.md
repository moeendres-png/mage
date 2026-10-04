# C12 method-bound corpus and test-resource bytecode, 2026-10-03

This closes two Codex P1 findings on mage#39:

- **"Bind the baseline to individual test methods"** (`corpus_policy.py:132`). The baseline (schema /2) now lists every enabled test method of every baseline class. A retained class that loses, renames, un-annotates or disables a baseline method is FAIL `baseline_test_method_removed`, unless the default branch approves the removal first. The static reading is not the authority: every required method must also be reported started by the trusted driver, which attributes each method to its declaring class. Otherwise the verdict is FAIL `required_test_methods_not_started`.
- **"Prevent resources from overwriting trusted-compiled tests"** (`witness.py:178`). `.class` files in test resources are no longer copied next to trusted-compiled bytecode. After resources are copied, every compiled class must be byte-identical, and no class may be added.

The third open P1, "Reject malformed counters before aggregating them" (`witness.py:460`), was already closed by `e293f031`: `decide` validates every raw per-module counter (CTRL-55).

## Evidence

- `SELFTEST-65-controls.json.gz`: the full gate selftest (every control row with its reasons), `SELFTEST = PASS (65/65)`, 0 not run.
  - It ran on commit `8752811b`, whose trusted Python and Java code is identical to the pushed head.
  - It ran in a local container: the trusted side as root, the existing unprivileged account `nobody` as the candidate account, offline Maven.
  - It did **not** run in GitHub Actions. The hosted run on the PR head is still required.
- `CTRL-66-mutation-fail-before.json`: with only the fix reverted, CTRL-66 observes **PASS**, so the forged bytecode was credited. With the fix it observes FAIL.
- CTRL-56 fail-before is the earlier reproduction in `../c12-independent-review-20261003/within-class-shrink`: ten methods cut to one received PASS.
- `counter-fixture-*` and `counter-fixture.bundle`: the counter-contract positive witness, regenerated through the full pipeline by `regenerate_counter_fixture.py` because the earlier fixture predates method binding. The earlier fixture remains in `../c12-independent-review-20261003`.

## Coverage on Mage master `6a2422d7`

Inside the 1997 baseline classes, every `@Test`-family annotation outside comments and literals maps to exactly one enumerated method: 6974 annotated methods plus one JUnit 3 method. 6835 are enabled, 140 disabled.

## Not claimed

- `C12_RUNTIME` on the real Mage corpus remains UNKNOWN: C12 has never run on the full corpus in Actions.
- 23 baseline classes have no enabled method (abstract or base classes, fully ignored classes). They cannot be "entered" under the existing class rule, so the first real-corpus run may FAIL on them. That outcome would be a real finding, not a pass.
- Test bodies are not bound.
