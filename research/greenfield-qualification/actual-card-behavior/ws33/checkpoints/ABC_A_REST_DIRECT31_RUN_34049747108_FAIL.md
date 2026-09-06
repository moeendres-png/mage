# WS33 ABC — A-rest Direct31 corrected mana lifecycle diagnostic run 34049747108 — terminal FAIL

Status: **FAIL_CLOSED**
Classification: **DIRECTLY_VERIFIED runtime + CODE_DERIVED qualification-pilot/cancellation-boundary defect**
Forge Rules Core defect: **NOT PROVEN**
Coverage promotion: **FALSE**
Coverage mutated during witness: **FALSE**

## Frozen lineage

- source HEAD: `6953607ff45cb89bb3748a0c96d36bb70c396801`
- source TREE: `f6ec854e527445645150b0283a9380915127fcf7`
- run: `34049747108`
- job: `101531078646`
- Forge pin: `8c7e9afb8e6caee88644b94e25da5852e36f8928`
- topology artifact: `9980023181`
- runtime artifact: `9994224909`
- runtime artifact digest: `sha256:0f79e66da701e6793adcfae62183e6b686a7dc4b03e2ceac2aab756d2cf07846`
- downloaded ZIP SHA-256 independently matched the GitHub digest exactly.

## Terminal runtime result

Exact Direct31 record set: `31` paths.

- record PASS: `28`
- record FAIL: `3`
- replay: **NOT ADMITTED** because the record gate failed closed
- coverage promotion: `0`

Failed exact paths:

1. `forge-behavior-v2:7365d5c90f364445ba2b22da9f1998aaf50fa394` — Disperse
2. `forge-behavior-v2:c20d354ac8258ea3088607c1c8bd7bbf3dab44ec` — Buried Ruin
3. `forge-behavior-v2:dd2f9dfad2fba886a0fa66300b8ab654ad501b86` — River's Rebuke

The record gate reports exactly these three status failures plus their expected no-stack/source-root consequences. No hidden-information leak or unrelated target-stage failure was established.

## Corrected observation-only mana lifecycle evidence

The corrected `InputPayMana.driveExternal()` observer changes no option, selection, mana/cost state, or boolean. It exposes the already-computed Forge-owned action list and selected server-mapped action token.

### Disperse

- unpaid cost starts `{1}{U}`
- authoritative actions include filtered mana abilities and `CANCEL`
- qualification pilot selects `ABILITY:62`, host `Sol Ring`, reducing cost to `{U}`
- next authoritative actions contain blue-payable abilities plus `CANCEL`
- qualification pilot selects `CANCEL`
- payment exits incomplete

### Buried Ruin

- unpaid mana component starts `{2}`
- authoritative actions include filtered pool/mana-ability transitions and `CANCEL`
- qualification pilot selects `CANCEL` immediately
- payment exits incomplete

### River's Rebuke

- unpaid cost starts `{4}{U}{U}`
- qualification pilot selects four Forge-filtered Forest mana abilities, reducing to `{U}{U}`
- then selects an Island mana ability, reducing to `{U}`
- next authoritative actions contain blue-payable abilities plus `CANCEL`
- qualification pilot selects `CANCEL`
- payment exits incomplete

Therefore the prior uncertainty is resolved: the seeded resources and Forge immediate payment transitions are sufficient to make progress. The observed failures occur when the qualification pilot chooses the explicit cancellation transition before full payment.

## Exact source adjudication

The immutable WS01 source `bf089ea806f54a9bbb64ede205915729e3629684`, file `apply-ws01-mana-convoke-bridge.py`, constructs `actions` from Forge-filtered floating mana and mana abilities, optional life, and — when `!mandatory` — appends the literal `CANCEL` token. It then calls:

`chooseExternalUiOptions(actions, 1, 1, false, false, "MANA_PAYMENT", value -> value)`

Thus cancellation is encoded as an ordinary discrete option while the request-level cancel flag is false. The inherited qualification pilot deterministically hashes/sorts the authoritative options and has no path-exercise policy that excludes the explicit cancellation transition. Selecting `CANCEL` is accepted and `InputPayMana` invokes `onCancel()` and returns.

This is not evidence that the pilot must infer mana legality. It must not. All non-cancel payment transitions are already Forge-filtered and revalidated by `InputPayMana`.

## Repair boundary

The next repair must be systemic and must preserve Rules-Core authority. Two acceptable forms require fresh qualification:

1. normalize the Forge-owned external decision boundary so cancellation is represented by request cancellation semantics rather than as an ordinary payment option; or
2. for qualification-only path exercise, add an explicit `MANA_PAYMENT` policy that chooses only among Forge-owned non-cancel transitions while such transitions exist, without evaluating colors, costs, or mana feasibility itself.

No card-name branch, mana legality engine, first/default/random option fallback, direct mana-pool injection, CostPayment bypass, manual targets, direct resolve, or coverage promotion is permitted.
