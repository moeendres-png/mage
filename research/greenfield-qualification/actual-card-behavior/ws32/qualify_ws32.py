#!/usr/bin/env python3
"""WS32 production CARD_BEHAVIOR_FAILURE hard gate."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
WS26_HEAD = "206a39cbaa3eeb98b10c2ddc36d51fe5b1b2f5ef"
WS26_TREE = "837f445f78bb26462653c58baf1532e294151b10"
WS12_HEAD = "80743bdbc2950b00e422f3deb38f04111f30a4d4"
CATEGORY = "CARD_BEHAVIOR_FAILURE"


def canonical(value: Any) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--contract", type=Path, required=True)
    p.add_argument("--runtime", type=Path, required=True)
    p.add_argument("--forge-root", type=Path, required=True)
    p.add_argument("--overlay-source", type=Path, required=True)
    p.add_argument("--source-head", required=True)
    p.add_argument("--source-tree", required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()

    contract = load(args.contract)
    runtime = load(args.runtime)
    assert contract["$id"] == "commander-simulator-next.failure-outcome.v1"
    assert contract["x-categories"][CATEGORY]["production_reachable"] is True
    assert contract["x-categories"][CATEGORY]["state_commit"] == "FORBIDDEN"
    assert contract["x-categories"][CATEGORY]["public_message"] == "card behavior verification failed"

    assert runtime["schema"] == "commander-simulator-next.ws32-runtime-witness.v1"
    assert runtime["forge_pin"] == FORGE_PIN
    assert runtime["stdout_only"] is False
    assert runtime["fallback_used"] is False
    positive = runtime["positive"]
    mismatch = runtime["controlled_mismatch"]
    public = runtime["public_failure"]

    assert positive["hook_calls"] == 1
    assert positive["stack_empty_at_hook"] is True
    assert positive["semantic_match"] is True
    assert positive["expected_hand"] == positive["actual_hand"]
    assert positive["expected_library"] == positive["actual_library"]
    assert positive["staged_state_published"] is True

    assert mismatch["hook_calls"] == 1
    assert mismatch["stack_empty_at_hook"] is True
    assert mismatch["semantic_match"] is False
    assert mismatch["expected_hand"] != mismatch["actual_hand"]
    assert mismatch["expected_library"] == mismatch["actual_library"]
    assert mismatch["engine_execution"] == "PASS_BEFORE_CONTROLLED_VERIFIER_FAILURE"
    assert mismatch["staged_state_published"] is False

    allowed_public = set(contract["properties"])
    required_public = set(contract["required"])
    forbidden_public = {"expected", "actual", "semantic_path", "trace_sha256", "witness_id", "primitive_id", "oracle_id", "card_name", "hand", "library", "zone"}
    assert set(public).issubset(allowed_public)
    assert required_public.issubset(public)
    assert forbidden_public.isdisjoint(public)
    assert public["schema"] == contract["$id"]
    assert public["category"] == CATEGORY
    assert public["public_message"] == contract["x-categories"][CATEGORY]["public_message"]
    assert public["state_committed"] is False

    forge = args.forge_root.resolve()
    game_java = (forge / "forge-game/src/main/java/forge/game/Game.java").read_text(encoding="utf-8")
    stack_java = (forge / "forge-game/src/main/java/forge/game/zone/MagicStack.java").read_text(encoding="utf-8")
    mapper_java = (forge / "forge-gui/src/main/java/forge/gamemodes/match/input/UnifiedOutcomeMapper.java").read_text(encoding="utf-8")
    verifier_java = (forge / "forge-game/src/main/java/forge/game/CardBehaviorVerifier.java").read_text(encoding="utf-8")
    exception_java = (forge / "forge-game/src/main/java/forge/game/CardBehaviorVerificationException.java").read_text(encoding="utf-8")
    overlay_source = args.overlay_source.read_text(encoding="utf-8")

    hook_present = (
        "private CardBehaviorVerifier cardBehaviorVerifier;" in game_java
        and "game.verifyResolvedCardBehavior(sa);" in stack_java
        and "fromCardBehaviorFailure" in mapper_java
        and "CardBehaviorVerificationException" in mapper_java
    )
    hook_after_finish = stack_java.index("finishResolving(sa, thisHasFizzled);") < stack_java.index("game.verifyResolvedCardBehavior(sa);") < stack_java.index("game.copyLastState();", stack_java.index("game.verifyResolvedCardBehavior(sa);"))
    default_noop = "if (cardBehaviorVerifier != null)" in game_java
    production_text = "\n".join((verifier_java, exception_java, overlay_source))
    card_name_free = "Mulldrifter" not in production_text and "Storm Crow" not in production_text and "Sol Ring" not in production_text

    private_runtime = {
        "schema": "commander-simulator-next.ws32-production-binding.v1",
        "forge_pin": FORGE_PIN,
        "ws26_head": WS26_HEAD,
        "ws26_tree": WS26_TREE,
        "ws12_head": WS12_HEAD,
        "production_hook": runtime["production_hook"],
        "actual_card_runtime_path": runtime["actual_card_runtime_path"],
        "positive": positive,
        "controlled_mismatch": mismatch,
        "runtime_witness_sha256": sha256(args.runtime),
        "hook_present": hook_present,
        "hook_after_finish_resolving": hook_after_finish,
        "hook_disabled_by_default": default_noop,
        "card_name_production_branches": 0 if card_name_free else 1,
    }

    hard_gates = {
        "exact_forge_pin": runtime["forge_pin"] == FORGE_PIN,
        "actual_card_rules_core_path_executed": runtime["actual_card_runtime_path"].endswith("MagicStack.resolveStack->semantic verifier"),
        "positive_control_pass": positive["semantic_match"] is True and positive["hook_calls"] == 1,
        "production_hook_executed": mismatch["hook_calls"] == 1 and hook_present,
        "hook_is_post_resolution": mismatch["stack_empty_at_hook"] is True and hook_after_finish,
        "engine_execution_succeeded_before_mismatch": mismatch["engine_execution"] == "PASS_BEFORE_CONTROLLED_VERIFIER_FAILURE",
        "controlled_semantic_mismatch_detected": mismatch["semantic_match"] is False,
        "typed_card_behavior_failure": public["category"] == CATEGORY,
        "distinct_from_engine_failure": public["category"] != "ENGINE_FAILURE" and mismatch["engine_execution"].startswith("PASS"),
        "failed_state_not_published": mismatch["staged_state_published"] is False and public["state_committed"] is False,
        "silent_fallback_absent": runtime["fallback_used"] is False,
        "public_payload_hidden_info_safe": forbidden_public.isdisjoint(public),
        "public_payload_contract_shaped": set(public).issubset(allowed_public) and required_public.issubset(public),
        "production_hook_disabled_by_default": default_noop,
        "classification_not_card_name_based": card_name_free,
        "stdout_only_false": runtime["stdout_only"] is False,
    }
    assert all(hard_gates.values())

    gate = {
        "schema": "commander-simulator-next.ws32-card-behavior-production-binding.v1",
        "workstream": "WS32",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "base_head": WS26_HEAD,
        "base_tree": WS26_TREE,
        "forge_pin": FORGE_PIN,
        "ws12_contract_head": WS12_HEAD,
        "classification": CATEGORY,
        "evidence_class": "TECHNICALLY_CONFORMANT",
        "production_binding": "forge.game.zone.MagicStack#resolveStack post-finishResolving generic semantic verifier",
        "production_reachable": True,
        "engine_execution": "PASS",
        "semantic_verifier": "FAIL_AS_CONTROLLED",
        "state_committed": False,
        "fallback_used": False,
        "public_failure": public,
        "hard_gates": hard_gates,
        "CARD_BEHAVIOR_FAILURE": "PASS",
        "FAILURE_SEMANTICS_BLOCKER_CLOSED": True,
        "WORKSTREAM_COMPLETE": True,
        "architecture_freeze": "NOT_AUTHORIZED_BY_THIS_WORKSTREAM",
        "integration_status": "Q5_PENDING_INTEGRATION",
    }

    args.out.mkdir(parents=True, exist_ok=True)
    files = {
        "CARD_BEHAVIOR_FAILURE.json": public,
        "WS32_RUNTIME_BINDING.json": private_runtime,
        "WS32_GATE.json": gate,
    }
    for name, value in files.items():
        (args.out / name).write_bytes(canonical(value))
    hashes = [f"{sha256(args.out / name)}  {name}" for name in sorted(files)]
    (args.out / "WS32_HASHES.sha256").write_text("\n".join(hashes) + "\n", encoding="utf-8")

    print("WS32_CARD_BEHAVIOR_FAILURE=PASS")
    print("WS32_PRODUCTION_REACHABLE=TRUE")
    print("WS32_ENGINE_EXECUTION=PASS")
    print("WS32_SEMANTIC_VERIFIER=FAIL_AS_CONTROLLED")
    print("WS32_STATE_COMMITTED=FALSE")
    print("WS32_FALLBACK_USED=FALSE")
    print("WORKSTREAM_COMPLETE=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
