# WS33B Cost — terminal blocker registry (5 paths)

Status: TERMINAL_IN_PIN (independent adjudication required for any override).
Branch: work/ws33-b-high-throughput-20260907.
These 5 of 402 Cost paths cannot complete production payment in pinned Forge
(8c7e9afb8e6caee88644b94e25da5852e36f8928) because their cost Valid
expressions reference bindings with no production branch. The payment engine
fail-closes (returns false / matches nothing). No harness defect was found;
fixture shapes were verified against the engine source.

## Paths

1. forge-behavior-v2:83da92d042e1c29d770df07397319afb1a2acb9d — Conspiracy Theorist
   ExileFromGrave<1/Card.TriggeredCards>: `TriggeredCards` has zero matches
   in forge-game/forge-gui sources; the Valid never matches.
2. forge-behavior-v2:8671678f79ce684700bee73e1fedcbdd2cc4fa94 — Greenwarden of Murasa
   ExileAnyGrave<1/Card.TriggeredNewCard>: `TriggeredNewCard` appears only in
   hardcoded effect strings, never as a cost Valid binding.
3. forge-behavior-v2:f4c7f4744d2aafd7867c487427756616567b0177 — Cavalier of Thorns
   Same dead `TriggeredNewCard` binding as Greenwarden.
4. forge-behavior-v2:e45204fac7594e256cef247c35ef92defba2b797 — Foot Chopper
   Sac<1/Card.TriggeredSource/that creature>: `TriggeredSource` has zero
   matches as a card property in CardProperty.
5. forge-behavior-v2:fdfdd242632a5ba2208e4acace7b4500bb347efe — Blazing Torch
   T Sac<1/OriginalHost/Blazing Torch>: `OriginalHost/...` as a sacrifice
   Valid has no production branch (OriginalHost resolves only in defined-
   player/card contexts, never as a sacrifice filter).

## Treatment

These paths remain UNKNOWN. They are excluded from the B2 promotion set by
exact path-ID registry (see ws33_filter_abc_b2_cost_campaign.py
TERMINAL_BLOCKERS). Any future engine support reopens them; nothing in the
campaign masks their status.

## Classification

CODE_DERIVED (source reads) + DIRECTLY_VERIFIED (executed fail-closed
payment outcomes). No engine source was modified for these paths.
