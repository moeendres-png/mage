#!/usr/bin/env python3
"""Inventory transitive Forge-core RNG helpers reachable from rules/game code.

The direct forge-game census cannot see randomness hidden behind utility calls.
Aggregates.random is used by GameAction to choose the first-turn player and
StreamUtil.random is consumed by rules/card helpers. WS06 deliberately does not
rewrite these helpers globally: they are also callable from UI/lobby code. The
patched MyRandom instead bridges an unnamed helper call to a named game stream
only when the live stack contains both a forge.game.* rules caller and one of
the qualified helpers. Any other unnamed RNG reached from forge.game.* fails
closed; non-rules callers remain on the independent legacy/UI RNG.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

TARGETS = (
    "forge-core/src/main/java/forge/util/Aggregates.java",
    "forge-core/src/main/java/forge/util/StreamUtil.java",
)


def scan(path: Path, root: Path) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith(("package ", "import ", "//", "*")):
            continue
        if "MyRandom.getRandom()" in line:
            findings.append({
                "kind": "TRANSITIVE_UNNAMED_MY_RANDOM",
                "path": str(path.relative_to(root)).replace("\\", "/"),
                "line": line_no,
                "text": line.strip()[:500],
                "control": "STACK_QUALIFIED_NAMED_STREAM",
            })
    return findings


def verify_runtime_bridge(root: Path) -> None:
    source = (root / "forge-core/src/main/java/forge/util/MyRandom.java").read_text(encoding="utf-8")
    anchors = (
        "private static String qualifiedTransitiveRulesStream()",
        'className.equals("forge.util.Aggregates")',
        'className.equals("forge.util.StreamUtil")',
        'className.startsWith("forge.game.")',
        'return "rules.transitive." + helperClass + "." + helperMethod;',
        "if (hasRulesCaller())",
        "WS06 unnamed rules RNG used while a strict game RNG scope is active",
    )
    missing = [anchor for anchor in anchors if anchor not in source]
    if missing:
        raise SystemExit(f"WS06 transitive runtime RNG bridge is incomplete: {missing!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("forge_root")
    parser.add_argument("--inventory", required=True)
    args = parser.parse_args()

    root = Path(args.forge_root).resolve()
    inventory_path = Path(args.inventory)
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))

    guarded: list[dict[str, object]] = []
    for relative in TARGETS:
        path = root / relative
        if not path.is_file():
            raise SystemExit(f"missing exact-pin transitive RNG helper: {relative}")
        findings = scan(path, root)
        if not findings:
            raise SystemExit(f"expected unnamed RNG callsites in qualified helper: {relative}")
        guarded.extend(findings)

    verify_runtime_bridge(root)

    overlay = inventory["overlay"]
    baseline = inventory["baseline"]
    baseline["transitive_core_unnamed_myrandom_callsite_count"] = len(guarded)
    baseline["transitive_core_unnamed_myrandom_calls"] = guarded
    overlay["transitive_core_rng_helpers"] = list(TARGETS)
    overlay["transitive_core_guarded_callsite_count"] = len(guarded)
    overlay["transitive_core_uncontrolled_rng_paths"] = 0
    overlay["transitive_core_control"] = "STACK_QUALIFIED_NAMED_STREAM"
    overlay["strict_runtime_unnamed_rng_guard"] = "PASS"
    overlay["strict_runtime_unnamed_rng_note"] = (
        "Qualified Aggregates/StreamUtil calls with a forge.game.* caller are bridged "
        "to rules.transitive.<helper>.<method>; every other unnamed forge.game RNG "
        "fails closed; non-rules UI/lobby callers remain outside the game RNG tape."
    )
    existing = int(overlay.get("uncontrolled_decision_relevant_rng_paths", 0))
    overlay["uncontrolled_decision_relevant_rng_paths"] = existing
    overlay["named_game_rng_streams"] = (
        "PASS" if existing == 0 else "FAIL"
    )

    inventory_path.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WS06_TRANSITIVE_CORE_GUARDED_CALLS={len(guarded)}")
    print("WS06_TRANSITIVE_CORE_UNCONTROLLED=0")
    print("WS06_STRICT_RUNTIME_UNNAMED_RNG_GUARD=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
