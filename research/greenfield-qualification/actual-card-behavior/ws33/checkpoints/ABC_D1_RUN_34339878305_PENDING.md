# ABC-D1 lifegain run 34339878305 — PENDING (registered)

Date: 2026-09-09. Branch: `work/ws33-d-high-throughput-20260907`.
TERMINAL_RESULT=PENDING. COVERAGE_PROMOTION=FALSE. WRITE_FREEZE in effect
for D1 machinery/paths until terminal adjudication.

## Frozen run source

- SOURCE_HEAD=`a697d61dfa7a7217b4a153a69cc159ca1055d153`
  (contains: D1b FAIL adjudication + R1/R2 systemic repair)
- SOURCE_TREE=`TBD_AT_ADJUDICATION_VIA_RUN_HEAD_SHA`
- RUN=`34339878305` (head_sha verified equal to SOURCE_HEAD at registration)
- EXPECTED_ARTIFACT=`ws33-abc-d1-lifegain-34339878305`

## What changed vs D1b (narrow systemic repair only)

- R1: preparer reads exact `Name:` from pinned card scripts
  (`Zuran Orb`, `Ayli, Eternal Pilgrim`, `Angel's Mercy`, ...).
- R2: ACTIVATED_* driver places the witnessed host on the battlefield;
  Trading Post host removed from fixture table (cost fixtures only).
- `placeCard` guard converts opaque NPEs into named diagnostics.
- TARGET_DIGEST unchanged
  (`7de915711efb5e70387af86481f844bc701db7e4d448a5032255f71e5e6fbc40`,
  id-based); no workflow change needed. Preparer+filter dry-run
  locally PASS against pinned scripts.

## Frozen selection / deps

Same as D1b PENDING: 10 provable ids, 12 deferred, same Forge/WS01/
WS12/WS32 pins, same model artifact/manifest/consumer pins.

## Exact next action

Poll run 34339878305 to terminal; adjudicate artifact independently;
on PASS repartition exact validated paths and continue to D2 (LifeLose
061, surveyed: ~8 provable + ~10 deferred); on FAIL persist
root cause before any further mutation.
