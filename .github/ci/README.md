# Native Mage module signals (C13)

The existing full Maven reactor remains the `build` check. Its failure is retained.
The same run uploads `native-module-signals-<run>-<attempt>` containing the source
SHA/TREE, event head (distinct from the checkout merge SHA), per-module XML hashes
and counters. Jobs named `Mage.Tests` and `Mage.Verify` consume that same-run
artifact independently: a Verify failure cannot label successful Rules tests as
failed, and a Rules-test PASS cannot turn an overall reactor failure into PASS.
No duplicate Maven execution is added. A unique final reactor-summary line must confirm each module completed; partial
reports from an interrupted run cannot earn PASS. The reactor log digest is bound.
Missing/incomplete reports are NOT_RUN or
UNKNOWN and cause the corresponding check to fail. Zero executed tests, malformed
counters and inconsistent XML never produce a green signal.

These are native candidate-controlled report observations, not trusted C12
qualification evidence or proof of full coverage. `qualification_credit=false`
is explicit. Disabled coverage remains UNKNOWN pending C16, and Verify reference
binding remains UNKNOWN pending C14. A native green check does not discharge
those gaps. Lab intake must read the two module records and the original reactor
outcome separately; it must not infer overall qualification from either check.

Local controls: `python3 .github/ci/test_native_signals.py`. The full execution
proof is the exact-head hosted Maven run plus both dependent signal jobs/artifact.
No required check/ruleset, engine source, test assertion, provider pin or disabled
test policy is changed.

Maven runs with `-fae` (fail at end), so a failing `Mage.Tests` does not stop
`Mage.Verify` from running: each check reports its own module's outcome, and the
overall `build` result is still failure. Collection and the two checks run after
a failure but not after a cancellation; a cancelled run yields no signal.
