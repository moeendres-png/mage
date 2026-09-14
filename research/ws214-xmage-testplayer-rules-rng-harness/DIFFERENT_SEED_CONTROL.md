# WS214 Different-Seed Control (post-fix)

- In-JVM (t6): seed 0x5EED214A vs 0xBEEF214B mixed sequences differ;
  consumption shape identical (32 == 32).
- Fresh-JVM (t10, pids 754946 / 754969):
  CONTROL-A coins=T,H,T,T,H,T,H,T,T,H,T,H,H,T,T,T vs
  CONTROL-B coins=H,H,T,H,H,T,T,T,T,T,T,T,H,T,H,T — differ;
  callsAfter=32 in both; harness==ctrl in both processes.
- Pre-fix note: seed control also "passed" pre-fix (via RandomUtil), so this
  control alone never proved correctness — it is meaningful only together
  with same-seed equality + accounting, which failed pre-fix and pass post-fix.

DIFFERENT_SEED_CONTROL = YES (seed influence demonstrated, shape preserved).
