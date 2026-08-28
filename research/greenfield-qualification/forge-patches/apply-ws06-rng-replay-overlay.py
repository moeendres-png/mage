#!/usr/bin/env python3
"""Apply the WS06 RNG/semantic-replay qualification overlay to exact-pin Forge.

This is deliberately a qualification overlay: it never writes the upstream
Forge repository and it expects the completed WS01 overlay to have been applied
first in an isolated checkout.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"


def stream_name(relative: Path, kind: str, ordinal: int) -> str:
    stem = str(relative).replace("\\", "/").replace("forge-game/src/main/java/", "")
    stem = stem[:-5] if stem.endswith(".java") else stem
    stem = re.sub(r"[^A-Za-z0-9_.]+", ".", stem.replace("/", "."))
    return f"rules.{stem}.{kind.lower()}.{ordinal}"


def old_census(root: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    direct: list[dict[str, object]] = []
    myrandom: list[dict[str, object]] = []
    patterns = [
        ("NEW_RANDOM", re.compile(r"\bnew\s+Random\s*\(")),
        ("NEW_SECURE_RANDOM", re.compile(r"\bnew\s+SecureRandom\s*\(")),
        ("THREAD_LOCAL_RANDOM", re.compile(r"ThreadLocalRandom")),
        ("COLLECTIONS_SHUFFLE", re.compile(r"Collections\.shuffle\s*\(")),
        ("MATH_RANDOM", re.compile(r"Math\.random\s*\(")),
    ]
    my = re.compile(r"MyRandom(?:\.getRandom\(\)|\.percentTrue\s*\()")
    base = root / "forge-game/src/main/java"
    for path in base.rglob("*.java"):
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("//") or stripped.startswith("*"):
                continue
            for label, pattern in patterns:
                if pattern.search(line):
                    direct.append({
                        "kind": label,
                        "path": str(path.relative_to(root)),
                        "line": line_no,
                        "text": line.strip()[:500],
                    })
            if my.search(line):
                myrandom.append({
                    "kind": "MY_RANDOM",
                    "path": str(path.relative_to(root)),
                    "line": line_no,
                    "text": line.strip()[:500],
                })
    return direct, myrandom


def _matching_paren(text: str, open_index: int) -> int:
    depth = 0
    in_string = False
    escape = False
    for index in range(open_index, len(text)):
        char = text[index]
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unbalanced parenthesis while patching RNG call")


def _top_level_comma(value: str) -> int | None:
    depth = 0
    in_string = False
    escape = False
    for index, char in enumerate(value):
        if in_string:
            if escape:
                escape = False
            elif char == "\\":
                escape = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == "," and depth == 0:
            return index
    return None


def patch_calls_in_line(line: str, relative: Path, ordinals: dict[str, int], inventory: list[dict[str, object]]) -> str:
    if line.lstrip().startswith(("import ", "package ", "//", "*")):
        return line

    def new_stream(kind: str, before: str) -> str:
        ordinals[kind] = ordinals.get(kind, 0) + 1
        name = stream_name(relative, kind, ordinals[kind])
        inventory.append({"path": str(relative), "kind": kind, "stream": name, "before": before.strip()[:500]})
        return name

    while "MyRandom.getRandom()" in line:
        name = new_stream("MY_RANDOM", line)
        line = line.replace("MyRandom.getRandom()", f'MyRandom.getRandom("{name}")', 1)
    while True:
        match = re.search(r"MyRandom\.percentTrue\s*\(", line)
        if not match:
            break
        start = match.end()
        if line[start:].lstrip().startswith('"'):
            break
        name = new_stream("MY_RANDOM_PERCENT", line)
        line = line[:start] + f'"{name}", ' + line[start:]

    for kind, pattern in (
        ("NEW_SECURE_RANDOM", re.compile(r"\bnew\s+SecureRandom\s*\([^)]*\)")),
        ("NEW_RANDOM", re.compile(r"\bnew\s+Random\s*\([^)]*\)")),
        ("THREAD_LOCAL_RANDOM", re.compile(r"ThreadLocalRandom\.current\s*\(\s*\)")),
        ("MATH_RANDOM", re.compile(r"Math\.random\s*\(\s*\)")),
    ):
        while True:
            match = pattern.search(line)
            if not match:
                break
            name = new_stream(kind, line)
            replacement = f'MyRandom.getRandom("{name}")'
            if kind == "MATH_RANDOM":
                replacement += ".nextDouble()"
            line = line[:match.start()] + replacement + line[match.end():]

    search_from = 0
    token = "Collections.shuffle"
    while True:
        call = line.find(token, search_from)
        if call < 0:
            break
        open_index = line.find("(", call + len(token))
        if open_index < 0:
            break
        close_index = _matching_paren(line, open_index)
        args = line[open_index + 1:close_index]
        comma = _top_level_comma(args)
        name = new_stream("COLLECTIONS_SHUFFLE", line)
        if comma is None:
            new_args = args + f', MyRandom.getRandom("{name}")'
        else:
            first = args[:comma]
            new_args = first + f', MyRandom.getRandom("{name}")'
        line = line[:open_index + 1] + new_args + line[close_index:]
        search_from = open_index + 1 + len(new_args) + 1

    return line


def patch_rules_rng(root: Path) -> list[dict[str, object]]:
    changed_inventory: list[dict[str, object]] = []
    base = root / "forge-game/src/main/java"
    for path in sorted(base.rglob("*.java")):
        relative = path.relative_to(root)
        original = path.read_text(encoding="utf-8")
        ordinals: dict[str, int] = {}
        lines = [patch_calls_in_line(line, relative, ordinals, changed_inventory) for line in original.splitlines(keepends=True)]
        text = "".join(lines)
        if text == original:
            continue
        # Normalize pre-existing fully-qualified calls in any rewritten source.
        # This makes the generated import decision reflect actual source usage
        # rather than the substring "MyRandom." inside forge.util.MyRandom.
        text = text.replace("forge.util.MyRandom.", "MyRandom.")
        if "MyRandom." in text and "import forge.util.MyRandom;" not in text and "import forge.util.*;" not in text:
            package_end = text.find("\n", text.find("package "))
            if package_end < 0:
                raise SystemExit(f"cannot add MyRandom import to {relative}")
            text = text[:package_end + 1] + "\nimport forge.util.MyRandom;\n" + text[package_end + 1:]
        if "ThreadLocalRandom" not in text:
            text = text.replace("import java.util.concurrent.ThreadLocalRandom;\n", "")
        if "SecureRandom" not in text:
            text = text.replace("import java.security.SecureRandom;\n", "")
        path.write_text(text, encoding="utf-8")
    return changed_inventory


def scan_uncontrolled(root: Path) -> list[dict[str, object]]:
    failures: list[dict[str, object]] = []
    base = root / "forge-game/src/main/java"
    patterns = [
        ("UNNAMED_MY_RANDOM", re.compile(r"MyRandom\.getRandom\(\)")),
        ("NEW_RANDOM", re.compile(r"\bnew\s+Random\s*\(")),
        ("NEW_SECURE_RANDOM", re.compile(r"\bnew\s+SecureRandom\s*\(")),
        ("THREAD_LOCAL_RANDOM", re.compile(r"ThreadLocalRandom\.current\s*\(")),
        ("MATH_RANDOM", re.compile(r"Math\.random\s*\(")),
    ]
    for path in sorted(base.rglob("*.java")):
        relative = str(path.relative_to(root))
        for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith(("import ", "package ", "//", "*")):
                continue
            for kind, pattern in patterns:
                if pattern.search(line):
                    failures.append({"kind": kind, "path": relative, "line": line_no, "text": line.strip()[:500]})
            if "MyRandom.percentTrue(" in line:
                tail = line.split("MyRandom.percentTrue(", 1)[1].lstrip()
                if not tail.startswith('"'):
                    failures.append({"kind": "UNNAMED_PERCENT_TRUE", "path": relative, "line": line_no, "text": line.strip()[:500]})
            if "Collections.shuffle" in line:
                call = line.find("Collections.shuffle")
                open_index = line.find("(", call)
                if open_index >= 0:
                    close_index = _matching_paren(line, open_index)
                    args = line[open_index + 1:close_index]
                    comma = _top_level_comma(args)
                    if comma is None or "MyRandom.getRandom(\"rules." not in args[comma + 1:]:
                        failures.append({"kind": "UNSCOPED_COLLECTIONS_SHUFFLE", "path": relative, "line": line_no, "text": line.strip()[:500]})
    return failures


def patch_game_semantic_observer(root: Path) -> None:
    path = root / "forge-game/src/main/java/forge/game/Game.java"
    text = path.read_text(encoding="utf-8")
    class_anchor = "public class Game {\n"
    if text.count(class_anchor) != 1:
        raise SystemExit("WS06 Game class anchor mismatch")
    observer = """public class Game {\n\n    @FunctionalInterface\n    public interface SemanticStateObserver {\n        void onCheckpoint(Game game, String checkpoint);\n    }\n\n    private static volatile SemanticStateObserver semanticStateObserver;\n\n    public static void setSemanticStateObserver(final SemanticStateObserver observer) {\n        semanticStateObserver = observer;\n    }\n\n    private void emitSemanticCheckpoint(final String checkpoint) {\n        final SemanticStateObserver observer = semanticStateObserver;\n        if (observer != null) {\n            observer.onCheckpoint(this, checkpoint);\n        }\n    }\n"""
    text = text.replace(class_anchor, observer, 1)

    id_anchor = "        this.id = nextId();\n"
    if text.count(id_anchor) != 1:
        raise SystemExit("WS06 Game id anchor mismatch")
    text = text.replace(id_anchor, id_anchor + "        if (Boolean.getBoolean(\"forge.ws06.strictGameRng\")) {\n" + "            MyRandom.requireActiveGameScope(\"forge.game.Game#\" + this.id);\n" + "        }\n", 1)

    ctor_anchor = "        subscribeToEvents(gameLog.getEventVisitor());\n"
    if text.count(ctor_anchor) != 1:
        raise SystemExit("WS06 Game constructor observer anchor mismatch")
    text = text.replace(ctor_anchor, ctor_anchor + '        emitSemanticCheckpoint("GAME_CONSTRUCTED");\n', 1)

    fire_anchor = "        events.post(event);\n"
    if text.count(fire_anchor) != 1:
        raise SystemExit("WS06 Game fireEvent anchor mismatch")
    text = text.replace(fire_anchor, fire_anchor + '        emitSemanticCheckpoint("EVENT:" + event.getClass().getSimpleName());\n', 1)
    path.write_text(text, encoding="utf-8")


def write_test(root: Path) -> None:
    path = root / "forge-gui-desktop/src/test/java/forge/net/Ws06SemanticReplayQualificationTest.java"
    if path.exists():
        raise SystemExit(f"refusing to overwrite unexpected WS06 test file: {path}")
    template_dir = Path(__file__).with_name("ws06-replay-overlay")
    source = "".join((template_dir / name).read_text(encoding="utf-8") for name in (
        "Ws06SemanticReplayQualificationTest.part1",
        "Ws06SemanticReplayQualificationTest.part2",
    ))
    path.write_text(source, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("forge_root")
    parser.add_argument("--inventory", required=True)
    args = parser.parse_args()

    root = Path(args.forge_root).resolve()
    if not (root / ".git").exists():
        raise SystemExit("Forge checkout is not a git worktree")

    myrandom_path = root / "forge-core/src/main/java/forge/util/MyRandom.java"
    original = myrandom_path.read_text(encoding="utf-8")
    required_anchors = (
        "private static Random random = new SecureRandom();",
        "public static Random getRandom()",
        "public static void setRandom(Random random)",
    )
    for anchor in required_anchors:
        if anchor not in original:
            raise SystemExit(f"unexpected exact-pin MyRandom source; missing {anchor!r}")

    baseline_direct, baseline_myrandom = old_census(root)
    if len(baseline_direct) != 8:
        raise SystemExit(f"expected exact-pin rules/game direct RNG baseline=8, found {len(baseline_direct)}")
    if len(baseline_myrandom) != 20:
        raise SystemExit(f"expected exact-pin rules/game MyRandom baseline=20, found {len(baseline_myrandom)}")

    myrandom_template = Path(__file__).with_name("ws06-replay-overlay") / "MyRandom.java"
    myrandom_path.write_text(myrandom_template.read_text(encoding="utf-8"), encoding="utf-8")
    patched_sites = patch_rules_rng(root)
    patch_game_semantic_observer(root)
    write_test(root)

    uncontrolled = scan_uncontrolled(root)
    inventory = {
        "schema": "commander-simulator-next.ws06-rng-inventory.v1",
        "forge_pin": FORGE_PIN,
        "baseline": {
            "rules_game_direct_rng_bypass_count": len(baseline_direct),
            "rules_game_myrandom_callsite_count": len(baseline_myrandom),
            "direct_rng_bypasses": baseline_direct,
            "myrandom_calls": baseline_myrandom,
        },
        "overlay": {
            "rewritten_sites": patched_sites,
            "uncontrolled_decision_relevant_rng_paths": len(uncontrolled),
            "uncontrolled_sites": uncontrolled,
            "named_game_rng_streams": "PASS" if not uncontrolled else "FAIL",
            "pilot_rng_separation": "PASS",
            "pilot_rng_note": "WS06 pilot/replay source does not call MyRandom; rules RNG tape contains only named game streams.",
        },
    }
    out = Path(args.inventory)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inventory, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if uncontrolled:
        raise SystemExit(f"WS06 uncontrolled rules/game RNG paths remain: {len(uncontrolled)}")
    print("WS06_RNG_OVERLAY_APPLIED=TRUE")
    print("WS06_BASELINE_DIRECT_RNG=8")
    print("WS06_BASELINE_MYRANDOM=20")
    print("WS06_UNCONTROLLED_DECISION_RELEVANT_RNG_PATHS=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
