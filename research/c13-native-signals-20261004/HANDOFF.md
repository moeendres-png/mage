# C13 native signal repair

Before head19837eff7a2b9f41c4e415172141124102d9fef7: real hosted artifact
11301146989 in run37195645027 reported both modules UNKNOWN because Maven
prints version1.4.61 in final summaries. FIRST_HOSTED.json binds exact artifact
ZIP digest and raw identity; download via GitHub artifact API is reproducible.
The actual Mage.Tests counts were6821/0failures/0errors/125skipped;
Mage.Verify28/2failures/0errors/8skipped. This does not claim all disabled tests
ran or that references are current. Verify failure remains a C14 obligation.

The malformed consumer also admitted PASS for reports=[{}] and impossible skip
totals. This is retained in malformed-consumer-BEFORE.json. The consumer now
re-collects the extracted same-run XML/logs and compares the entire record,
including counts, paths, hashes, source/run and producer digest. 20 controls
pass, including component alterations, deleted/changed XML, changed log,
producer mismatch and actual versioned Maven lines. Reprocessing the unchanged
hosted bytes gives TestsPASS/VerifyFAIL; it is not a fresh build. New exact-head
hosted execution and independent review still required before merge.

Commands: python3 .github/ci/test_native_signals.py; collect --root ARTIFACT_ROOT
--out TEMP_JSON; signal --input ARTIFACT_ROOT/evidence/NATIVE_MODULE_SIGNALS.json
--module Mage.Tests or Mage.Verify --expected-sha596c105956811dab0a622fac4223f96312a90097
--expected-run37195645027. To reproduce repaired reprocessing, use current
collector and record its actual producer digest; old JSON remains historical.
No native observation is trusted qualification evidence.
