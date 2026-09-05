#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

PROVEN_EXTENSION_COMMIT = "8b97e92b68ddcc45929507cf9f055e0d928e97cf"
PROVEN_EXTENSION_PATH = "research/greenfield-qualification/actual-card-behavior/ws33/ws33_apply_target_fixture_catalog_extension.py"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_TARGET_FIXTURE_COMPOSITION=FAIL " + message)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preparer", type=Path, required=True)
    parser.add_argument("--test", type=Path, required=True)
    args = parser.parse_args()
    require(args.preparer.is_file(), f"missing preparer {args.preparer}")
    require(args.test.is_file(), f"missing test {args.test}")

    repo_root = Path(subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], text=True).strip())
    proven = subprocess.check_output(
        ["git", "-C", str(repo_root), "show", f"{PROVEN_EXTENSION_COMMIT}:{PROVEN_EXTENSION_PATH}"],
        text=True,
    )
    require("WS33_TARGET_FIXTURE_EXTENSION_SELECTOR_SHAPES=64" in proven,
            "pinned proven extension does not identify the 64-shape boundary")

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
        handle.write(proven)
        proven_script = Path(handle.name)
    try:
        subprocess.run([
            sys.executable, str(proven_script),
            "--preparer", str(args.preparer),
            "--test", str(args.test),
        ], check=True)
    finally:
        proven_script.unlink(missing_ok=True)

    cardinality = Path(__file__).with_name("ws33_apply_a1_cardinality_harness_repair.py")
    require(cardinality.is_file(), f"missing cardinality harness repair {cardinality}")
    subprocess.run([
        sys.executable, str(cardinality), "--test", str(args.test)
    ], check=True)

    print("WS33_TARGET_FIXTURE_COMPOSITION=PASS")
    print(f"WS33_TARGET_FIXTURE_PROVEN_COMMIT={PROVEN_EXTENSION_COMMIT}")
    print("WS33_TARGET_FIXTURE_MATERIALIZATION_LAYER=64_SHAPES")
    print("WS33_TARGET_FIXTURE_CARDINALITY_LAYER=FORGE_AUTHORITATIVE")
    print("WS33_TARGET_FIXTURE_SILENT_FALLBACK=FALSE")
    print("WS33_TARGET_FIXTURE_RULES_MUTATION=FALSE")


if __name__ == "__main__":
    main()
