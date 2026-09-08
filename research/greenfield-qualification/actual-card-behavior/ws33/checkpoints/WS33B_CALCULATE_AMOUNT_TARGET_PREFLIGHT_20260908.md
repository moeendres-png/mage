CANONICAL_HEAD = 6da237b704ba5e66c58c2334f47e36ef68ca980d
CANONICAL_TREE = 8f6d0151e4a9095c95925d6f6065214d382bf1dc
B_HEAD = 895240f4058076764227a418ad28e84f61d3a7ed
B_TREE = cec73ae51b0168280ea648892f3e9edd46dcd883
ALL_CALCULATE_AMOUNT_EFFECTIVE = 273
ALL_CALCULATE_AMOUNT_UNKNOWN = 273
B_OWNED_CALCULATE_AMOUNT_UNKNOWN = 273
OLD_377_EXPLANATION = stale 4276-registry cluster (202 ACTION + 158 TRIGGER + 16 CONTINUOUS + 1 COMBAT = 377, all unproved) fully superseded by consumer-aware re-derivation: canonical 4188 ledger holds 273 calculateAmount paths, 100% ACTION_COST_DECISION / WS33B / UNKNOWN, with ZERO ID overlap vs the 377 stale IDs (all 377 dropped in the 4276->4188 regeneration, all 273 are new IDs); 175 of the -104 gap is non-ACTION scope exit, remainder is model re-key/cardinality change; already-PASS filtering contributes 0 (0 calc PASS in base ledger; successor G81/A1-122 promotions are target/family-disjoint from calc, 0 overlap proven)
EXPECTED_273_CONFIRMED = TRUE
TARGET_SELECTOR = logical_bucket=WS33B AND implementation_target=forge.game.ability.AbilityUtils#calculateAmount AND current_status=UNKNOWN over WS33_INTEGRATED_CLOSURE_LEDGER.jsonl (4188 rows, repair_commit 991486fd012463d29173a9aba15ebb3296d64dda); B shard total 675 = 273 calculateAmount + 402 forge.game.cost.Cost
TARGET_LIST_HASH = sha256hex(sorted 273 effective_path_ids, LF-joined with trailing newline) = 30dd81f733e0c1dfdb2d3020c0b9b1e0a2ed542fcf78123d641839fb24800024
NEXT_IMPLEMENTATION_CLUSTER = 273-ID B-owned AbilityUtils#calculateAmount UNKNOWN set (first WS33B runtime-witness cluster; implementation not started)
