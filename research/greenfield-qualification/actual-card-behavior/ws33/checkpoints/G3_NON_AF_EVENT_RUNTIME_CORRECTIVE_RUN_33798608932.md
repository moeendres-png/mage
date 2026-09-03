# G3 NON-AF EVENT RUNTIME — SECOND CORRECTIVE RUN CHECKPOINT

Status: `QUEUED/RUNNING / UNADJUDICATED`

Evidence classification: `UNKNOWN` until full run and artifact adjudication.

## Run identity

- workflow source HEAD: `26ec46d852a731054e8719e5bf1ea37bef3f6ea6`
- workflow source TREE: `793c1e3c10cf07f4d0b432a56aa0f90e73eb7fe0`
- run: `33798608932`
- job: `100792262743`
- observed state at checkpoint creation: `queued`

## Single repair embodied by source HEAD

`apply-ws33-stack-resolution-reachability.py` now binds the exact pinned Forge `MagicStack` class declaration:

```java
public class MagicStack /* extends MyObservable */ implements Iterable<SpellAbilityStackInstance> {
```

The observer remains observation-only and positioned at the existing non-fizzled API-resolution boundary immediately before `AbilityUtils.resolve(sa)`.

No behavior coverage is promoted by this repair.

## Resume rule

Adjudicate run `33798608932` / job `100792262743` before any subsequent repair or retry. Persist the first material result, run/artifact identities and evidence classification before changing code.
