# WS33 G3 non-AF — Principal transport stack root cause

Status: DIRECTLY_VERIFIED / CODE_DERIVED

Canonical branch at diagnosis:

- HEAD: `81aec3765348b10d3ebcfdc2347aa0b95719117b`
- TREE: `e5f81fe53186b9a2ce32cbe44248cb69dfc5842b`

Last terminal event-runtime evidence:

- RUN: `33851809027`
- JOB: `100956085252`
- ARTIFACT: `9928708015`
- DIGEST: `sha256:65dfc40f374e63bd67150a2bf77285358c38e9d25026102f11a9eef5909077e0`

## Confirmed material progression

The previously blocked `Ingenious Smith / ChangesZone / TrigDig -> Dig` parent now reaches `admission/binding/execution = 1/1/1` after the non-discretionary singleton `getAbilityToPlay` repair.

The next failure is inside the executed Dig path and is an external hidden-card observation boundary:

`UNSUPPORTED_DECISION_PATH: hidden authoritative Card choices require RemoteClient principal observation`

The record tape already contains an accepted `ENTITY_MULTI_SELECTION` request for actor/principal `1`; therefore the failure is beyond the old trigger-play blocker and occurs in the hidden-card observation/lifetime stack around actual Card choices.

## Root cause

Pinned Forge `DigEffect` opens the real chooser visibility lifetime with `tempShowCards(top)` immediately before `chooseEntitiesForEffect(...)` and later closes it with `endTempShowCards()`.

The already-qualified Direct-G principal-observation v4 and G-SVar-AF principal-observation v5 runtime stacks both apply, in order after `apply-ws33-input-confirm.py`:

1. `runtime-overlays/apply-ws33-observation-fanout.py`
2. `runtime-overlays/apply-ws33-external-card-decision-lifetime.py`

Those overlays preserve Forge's existing may-look lifetime, synchronize the principal-scoped `RemoteClientGuiGame` projection before the external Card decision, synchronize redaction afterward, and close an already-open Forge temp-show scope at authoritative request return. They do not create legal options, choose an option, change RNG, or introduce a pilot fallback.

The current `ws33-g3-svar-event-runtime.yml` applies `apply-ws33-input-confirm.py` but omits both of those already-qualified overlays.

The affected event parent is executed by `Bob (Remote)` and the accepted decision request uses actor/principal `1`. Stable Direct-G principal-observation evidence has already qualified RemoteClient principal observation for principal `1` in the same 4P network topology. The missing capability is therefore the omitted qualified observation/lifetime overlay stack, not an actor-index or local-host substitution.

## Authorized narrow repair

Modify only `.github/workflows/ws33-g3-svar-event-runtime.yml` to:

- add the two overlay files to the workflow path filter;
- apply `apply-ws33-observation-fanout.py` immediately after `apply-ws33-input-confirm.py`;
- apply `apply-ws33-external-card-decision-lifetime.py` immediately after the fanout overlay;
- assert both overlays report PASS and preserve their fail-closed/zero-rules-mutation markers where available.

No new rules logic is authorized. No card/path-specific exception is authorized. No coverage promotion is authorized before a fresh single successor runtime run passes the existing 33-parent/32-path gates.
