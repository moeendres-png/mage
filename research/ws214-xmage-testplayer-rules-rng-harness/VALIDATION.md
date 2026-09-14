# WS214 Validation

- New harness qualification `WS214TestPlayerRulesRngTest`: 10/10 PASS
  post-fix (pre-fix: 4/10, with the 6 failures exactly the defect signature;
  see PRE_FIX_REPRODUCER.md). Covers: scripted coin/die precedence (t1/t2),
  unscripted coin stream + accounting (t3), unscripted die stream + boundaries
  d1/d20 (t4), mixed accounting (t5), different-seed control (t6), production
  parity vs `getRealPlayer()` delegate (t7), query-freeness (t8), fresh-JVM
  same-seed twins (t9), fresh-JVM different-seed control (t10).
- Fresh-JVM probes: separate `java` processes per digest (pids recorded);
  same-seed byte-identical incl. calls; different-seed diverges with same shape.
- WS212 regressions: 21/21 engine + 8/8 consumers PASS.
- Scripted card suites: FlipCoinTest 3/3, RollDiceTest 29/29 PASS.
- Mage.Tests full test-sourceset compiles clean (2033 files; only pre-existing
  deprecation/unchecked notes).
- Production-mutation guard: tracked diff = TestPlayer.java (2 method bodies +
  1 import) only; `git status` shows no production file touched; new files are
  `Mage.Tests/.../ws214/` (probe + test) and this evidence namespace.
- Checkstyle: NOT_RUN (no checkstyle binding in build; offline plugin
  resolution per workstream precedent — not claimed as PASS).
- FULL107 = NOT_RUN.
- GLOBAL_BEHAVIOR_CREDIT_CHANGE = 0. D5_TWIN_EQUALITY = UNKNOWN (Lab-side,
  WS213 question).
- PRODUCTION_RULES_CORE_CHANGE = NO.
