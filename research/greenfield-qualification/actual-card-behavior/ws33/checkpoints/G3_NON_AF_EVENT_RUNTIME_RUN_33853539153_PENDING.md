# WS33 G3 non-AF event runtime — pending successor

Status: PENDING / NOT YET ADJUDICATED

Qualified repair source:

- SOURCE_HEAD: `98bf38cf6c97f81faacfdefd40b718909ae5494d`
- SOURCE_TREE: `5fe6275585d6068d2fa92166fcf4693672b90c5b`
- RUN: `33853539153`
- JOB: `100961524939`

This is the first eligible successor after the invalid pre-runtime pin typo in run `33853430763`.

The workflow now restores the exact immutable Direct-G source pin:

`d8af15cb879bdfc3c40ce4cba3462da24ee3f272`

and adds only the already-qualified principal-observation/lifetime overlays to the non-AF event runtime stack:

1. `apply-ws33-observation-fanout.py`
2. `apply-ws33-external-card-decision-lifetime.py`

with explicit PASS / zero-rules-mutation / zero-pilot-fallback checks.

No coverage promotion is authorized until this run terminally proves the existing strict gates: 33 parent entrypoints, 32 effective paths, required Decision/RNG coverage, zero cross-principal leaks, and tape-driven semantic replay equality.
