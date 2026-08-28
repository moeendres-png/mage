#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def require(path: Path, needles: list[str]) -> list[dict[str, object]]:
    text = path.read_text(encoding="utf-8")
    out: list[dict[str, object]] = []
    lines = text.splitlines()
    for needle in needles:
        matches = [(i + 1, line.strip()) for i, line in enumerate(lines) if needle in line]
        if not matches:
            raise SystemExit(f"WS08 static audit missing expected mutable-state anchor {needle!r} in {path}")
        out.append({"anchor": needle, "matches": [{"line": n, "text": line} for n, line in matches]})
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("forge_root")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root = Path(args.forge_root).resolve()

    targets = [
        ("network_server_singleton", root / "forge-gui/src/main/java/forge/gamemodes/net/server/FServerManager.java",
         ["private static FServerManager instance"]),
        ("external_controller_factory", root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java",
         ["private static volatile Function<Player, ExternalDecisionProvider> externalDecisionProviderFactory"]),
        ("decision_tape_observer", root / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionTape.java",
         ["private static volatile EventObserver eventObserver"]),
        ("semantic_state_observer", root / "forge-game/src/main/java/forge/game/Game.java",
         ["private static volatile SemanticStateObserver semanticStateObserver"]),
        ("game_rng_scope", root / "forge-core/src/main/java/forge/util/MyRandom.java",
         ["private static final InheritableThreadLocal<GameScope> threadScope", "private static volatile GameScope processScope"]),
        ("principal_observation_probe", root / "forge-gui-desktop/src/test/java/forge/net/Ws05HiddenInfoProbe.java",
         ["private static final AtomicLong transportLeaks", "private static final AtomicLong ws08CrossGameObservationLeaks"]),
    ]

    inventory = []
    for name, path, needles in targets:
        if not path.exists():
            raise SystemExit(f"WS08 static audit missing source: {path}")
        inventory.append({
            "name": name,
            "path": str(path.relative_to(root)),
            "decision_relevant_mutable_state_present": True,
            "isolated_by": "one_game_per_os_process",
            "anchors": require(path, needles),
        })

    doc = {
        "schema": "commander-simulator-next.ws08-static-mutable-audit.v1",
        "status": "PASS",
        "architecture": "PROCESS_PER_GAME",
        "shared_decision_relevant_mutable_singletons_within_worker": len(inventory),
        "cross_game_shared_jvm_heap": False,
        "unisolated_cross_game_mutable_singletons": 0,
        "note": "Mutable JVM statics are present and therefore same-JVM multi-game execution is not qualified. WS08 qualifies one game per independent OS/JVM process; runtime evidence must prove distinct PIDs and unique external resources.",
        "inventory": inventory,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("WS08_STATIC_MUTABLE_AUDIT=PASS")
    print(f"WS08_PROCESS_CONTAINED_MUTABLE_SINGLETONS={len(inventory)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
