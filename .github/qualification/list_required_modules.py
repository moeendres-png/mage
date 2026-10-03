#!/usr/bin/env python3
"""Print the candidate modules that own required test classes, one per line.

Trusted default-branch source. Uses the same module-ownership rule as
``witness.py`` so the workflow resolves a classpath for exactly the modules the
witness will demand, and no others are silently assumed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from witness import enumerate_required_tests  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate-root", required=True)
    args = parser.parse_args()

    root = Path(args.candidate_root).resolve()
    if not root.is_dir():
        print("candidate root does not exist: {}".format(root), file=sys.stderr)
        return 2

    modules = sorted({entry["module"] for entry in enumerate_required_tests(root)})
    for module in modules:
        print(module)
    return 0


if __name__ == "__main__":
    sys.exit(main())