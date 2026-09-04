# WS33 G3 spawned-trigger diagnostic anchor root cause — 2026-09-04

Classification: `CODE_DERIVED / PRE-RUNTIME TOOLING DEFECT`

Pinned Forge: `8c7e9afb8e6caee88644b94e25da5852e36f8928`.

Run `33856299908` failed before harness/runtime execution because the observation-only patcher attempted to replace the entire pinned `TriggerHandler.canRunTrigger(...)` method using an exact string anchor.

The anchor omitted one existing pinned comment line inside the `TriggerType.Always` branch:

`// don't trigger again.`

Therefore `replace_once(...)` correctly failed closed with match count 0. No Forge boolean expression or runtime behavior was evaluated or changed by this run.

Repair scope is exactly one diagnostic-source correction: make the anchor byte-match the pinned method by restoring that omitted comment line. Do not change any production expression, gate ordering, trigger legality, event facts, targets, costs, RNG, decisions, or Study Hall fixture behavior.

After the correction, allow exactly one event-runtime successor and immediately persist its RUN/JOB/SOURCE_HEAD/TREE. Study Hall remains UNKNOWN until same-run `WS33_TRIGGER_GATE` evidence identifies the actual spawned-trigger rejection gate.

`COVERAGE_PROMOTION = FALSE`
`WS33_COMPLETE = FALSE`
`TASK_COMPLETE = NO`
