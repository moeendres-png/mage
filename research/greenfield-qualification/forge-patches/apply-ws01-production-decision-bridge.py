#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-production-decision-bridge.py <forge-root>")
root = Path(sys.argv[1]).resolve()
path = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
text = path.read_text(encoding="utf-8")

old = '''    @Override
    public void autoPassCancel() {
        if (!mayAutoPass()) {
            return;
        }
'''
new = '''    @Override
    public void autoPassCancel() {
        if (hasExternalDecisionProvider()) {
            // Legacy GUI yield/autopass is not a game-rule decision. In strict
            // external mode every actual priority pass is exported explicitly
            // through PRIORITY_ACTION, so this UI automation must be inert.
            return;
        }
        if (!mayAutoPass()) {
            return;
        }
'''
count = text.count(old)
if count != 1:
    raise SystemExit(f"expected one autoPassCancel anchor, found {count}")
path.write_text(text.replace(old, new, 1), encoding="utf-8")
print("WS01_PRODUCTION_DECISION_BRIDGE_APPLIED=TRUE")
