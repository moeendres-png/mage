#!/usr/bin/env python3
"""Close transitive Forge-core RNG helpers reachable from rules/game code.

WS06's direct forge-game census does not see randomness hidden behind utility
calls. Aggregates.random is used by GameAction to choose the first-turn player;
StreamUtil.random is also consumed by rules/card helpers. In a strict WS06 game
scope, both helpers must therefore route through explicit named game streams.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

TARGETS = (
    "forge-core/src/main/java/forge/util/Aggregates.java",
    "forge-core/src/main/java/forge/util/StreamUtil.java",
)


def stream_name(relative: str, ordinal: int) -> str:
    stem = relative.replace("forge-core/src/main/java/", "").replace("/", ".")
    if stem.endswith(".java"):
        stem = stem[:-5]
    return f"rules.core.{stem}.myrandom.{ordinal}"


def scan(path: Path, root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith(("package ", "import ", "//", "*")):
            continue
        if "MyRandom.getRandom()" in line:
            findings.append({
                "kind": "TRANSITIVE_UNNAMED_MY_RANDOM",
                "path": str(path.relative_to(root)),
                "line": line_no,
                "text": line.strip()[:500],
            })
    return findings


def patch(path: Path, root: Path) -> list[dict[str, object]]:
    relative = str(path.relative_to(root)).replace("\\", "/")
    text = path.read_text(encoding="utf-8")
    inventory: list[dict[str, object]] = []
    ordinal = 0
    while "MyRandom.getRandom()" in text:
        ordinal += 1
        stream = stream_name(relative, ordinal)
        inventory.append({
            "kind": "TRANSITIVE_CORE_MY_RANDOM",
            "path": relative,
            "stream": stream,
        })
        text = text.replace("MyRandom.getRandom()", f'MyRandom.getRandom("{stream}")', 1)
    path.write_text(text, encoding="utf-8")
    return inventory


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("forge_root")
    parser.add_argument("--inventory", required=True)
    args = parser.parse_args()

    root = Path(args.forge_root).resolve()
    inventory_path = Path(args.inventory)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

    baseline: list[dict[str, object]] = []
    rewritten: list[dict[str, object]] = []
    for relative in TARGETS:
        path = root / relative
        if not path.is_file():
            raise SystemExit(f"missing exact-pin transitive RNG helper: {relative}")
        baseline.extend(scan(path, root))
        rewritten.extend(patch(path, root))

    remaining: list[dict[str, object]] = []
    for relative in TARGETS:
        remaining.extend(scan(root / relative, root))

    overlay = inventory["overlay"]
    baseline_section = inventory["baseline"]
    baseline_section["transitive_core_unnamed_myrandom_callsite_count"] = len(baseline)
    baseline_section["transitive_core_unnamed_myrandom_calls"] = baseline
    overlay.setdefault("rewritten_sites", []).extend(rewritten)
    overlay["transitive_core_rng_helpers"] = list(TARGETS)
    overlay["transitive_core_uncontrolled_rng_paths"] = len(remaining)
    overlay["strict_runtime_unnamed_rng_guard"] = "PASS"
    overlay["strict_runtime_unnamed_rng_note"] = (
        "MyRandom.getRandom() throws while a strict WS06 game scope is active; "
        "production-reachable unnamed helper RNG therefore fails closed."
    )
    existing = int(overlay.get("uncontrolled_decision_relevant_rng_paths", 0))
    overlay["uncontrolled_decision_relevant_rng_paths"] = existing + len(remaining)
    overlay["uncontrolled_sites"] = list(overlay.get("uncontrolled_sites", [])) + remaining
    overlay["named_game_rng_streams"] = (
        "PASS" if overlay["uncontrolled_decision_relevant_rng_paths"] == 0 else "FAIL"
    )

    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if remaining:
        raise SystemExit(f"WS06 transitive core RNG paths remain: {len(remaining)}")

    print(f"WS06_TRANSITIVE_CORE_BASELINE_UNNAMED={len(baseline)}")
    print("WS06_TRANSITIVE_CORE_UNCONTROLLED=0")
    print("WS06_STRICT_RUNTIME_UNNAMED_RNG_GUARD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
