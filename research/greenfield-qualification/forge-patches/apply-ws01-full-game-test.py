#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-full-game-test.py <forge-root>")
root = Path(sys.argv[1]).resolve()
path = root / "forge-gui-desktop/src/test/java/forge/net/ExternalDecisionFullGameQualificationTest.java"
if path.exists():
    raise SystemExit(f"refusing to overwrite unexpected existing file: {path}")
path.write_text('''package forge.net;\n\nimport org.testng.annotations.Test;\n\npublic final class ExternalDecisionFullGameQualificationTest {\n    @Test(timeOut = 360_000)\n    public void fullFourPlayerCommanderGameEmitsStrictDecisionTape() throws Exception {\n        final String output = System.getProperty("ws01.decisionTapePath");\n        if (output == null || output.isBlank()) {\n            throw new IllegalStateException("ws01.decisionTapePath system property is required");\n        }\n        ExternalDecisionFullGameRunner.main(new String[] { output });\n    }\n}\n''', encoding="utf-8")
print("WS01_FULL_GAME_TEST_APPLIED=TRUE")
