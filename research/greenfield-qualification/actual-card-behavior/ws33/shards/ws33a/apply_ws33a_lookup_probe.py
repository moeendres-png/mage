#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

OLD = '''            if (ability.getMinTargets() != 1 || ability.getMaxTargets() != 1) {
                continue;
            }
            matches.add(ability);
'''
NEW = '''            // WS33A lookup probe deliberately does not reject an exact actual-card
            // TargetRestrictions ability merely because its Forge-computed target
            // cardinality is not 1..1. Target legality/cardinality remains entirely
            // Forge-owned; the downstream conservative provider still fails closed
            // unless the designated target and DONE transition are actually offered.
            matches.add(ability);
'''


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("java_file", type=Path)
    args = parser.parse_args()
    path = args.java_file
    text = path.read_text(encoding="utf-8")
    if text.count(OLD) != 1:
        raise SystemExit("WS33A_LOOKUP_PATCH=FAIL expected exact min/max lookup anchor once")
    text = text.replace(OLD, NEW, 1)
    path.write_text(text, encoding="utf-8")
    print("WS33A_LOOKUP_PATCH=PASS")


if __name__ == "__main__":
    main()
