#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-compile-fixes.py <forge-root>")
root = Path(sys.argv[1]).resolve()
path = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
text = path.read_text(encoding="utf-8")
old = """        final Integer selected = chooseExternalDiscrete(choices, 1, 1, false, false,\n                \"PRIORITY_ACTION\", index -> index < 0\n                        ? \"PASS_PRIORITY\"\n                        : \"spellability:\" + abilities.get(index).getId());\n        if (selected.get(0) < 0) {\n            return null;\n        }\n        return List.of(abilities.get(selected.get(0)));\n"""
new = """        final List<Integer> selected = chooseExternalDiscrete(choices, 1, 1, false, false,\n                \"PRIORITY_ACTION\", index -> index < 0\n                        ? \"PASS_PRIORITY\"\n                        : \"spellability:\" + abilities.get(index).getId());\n        if (selected.get(0) < 0) {\n            return null;\n        }\n        return List.of(abilities.get(selected.get(0)));\n"""
if text.count(old) != 1:
    raise SystemExit("expected exactly one priority-selection typing anchor")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("WS01_COMPILE_FIXES_APPLIED=TRUE")
