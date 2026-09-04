# WS33 G3 non-AF Principal Observation — source runs PENDING

STATUS = PENDING
WRITE_FREEZE = TRUE

SOURCE_HEAD = a7e1d6b2863ba78ee738f25b6d33317cf05e5e94
SOURCE_TREE = 0c2695708994264fa1e6556bac5ead59ad521fad

Run cardinality observed immediately after source push = 2, not the intended 1.

Intended G3.5 run:
- RUN = 33929441452
- WORKFLOW = .github/workflows/ws33-g3-svar-event-principal-observation.yml
- NAME = WS33 G3 SVar non-AF principal observation
- STATUS_AT_CHECKPOINT = queued

Incidental compatibility/requalification run caused by modifying shared `ws33_instrument_g_principal_observations.py` (which is in AF-v5 workflow path filters):
- RUN = 33929441412
- WORKFLOW = .github/workflows/ws33-g3-svar-af-principal-observation-v5.yml
- NAME = WS33 G3 SVar AF principal observation v5
- STATUS_AT_CHECKPOINT = queued

This is a transactional protocol incident, not permission to launch any additional run. Do not create a third run from this source commit. Because the shared instrumentation changed, the incidental AF-v5 run is relevant compatibility evidence and must be terminally adjudicated before relying on prior AF principal-observation evidence under the modified shared tool.

NEXT_ACTION = WRITE_FREEZE. Wait for both exact-source runs to become terminal. Persist each terminal run/job/artifact/digest/independent ZIP SHA256 and first failure or exact PASS gates before any repair/write. If intended G3.5 fails, diagnose from exact artifact/logs and persist root cause before repair.
