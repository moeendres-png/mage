#!/usr/bin/env python3
"""C16 (commander-playtest-lab#497): Mage.Verify's disabled coverage, made explicit.

A green Mage.Verify run must not imply that checks it never executes were
executed. This reads the verifier's source and inventories:

* ``disabled_tests``: test methods carrying ``@Ignore`` (with the comment that
  gives the reason);
* ``skip_lists``: per skip list, every ``skipListAddName(LIST, set, name)``
  entry that suppresses a check for one card;
* ``opt_in_checks``: checks that are off unless a property enables them
  (for example the full ability-text comparison against MTGJSON).

``--check`` compares the inventory with the committed
``.github/ci/verify_coverage_gaps.json`` and fails on any difference. A gap
can therefore neither appear nor disappear silently: enabling a test,
dropping a skip entry or adding one all show up as a reviewed change to that
file. ``--write`` regenerates it. Every listed gap is reported as NOT_RUN for
that part of Mage.Verify, never as PASS.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "Mage.Verify" / "src" / "test" / "java" / "mage" / "verify" / "VerifyCardDataTest.java"
INVENTORY = ROOT / ".github" / "ci" / "verify_coverage_gaps.json"
SCHEMA = "mage.verify.coverage-gaps/1"

_IGNORE = re.compile(r"^\s*@Ignore\b(?:\s*\([^)]*\))?\s*(?://\s*(?P<reason>.*))?$")
_METHOD = re.compile(r"^\s*public\s+void\s+(?P<name>\w+)\s*\(")
_SKIP = re.compile(r'^\s*skipListAddName\(\s*(SKIP_LIST_\w+)\s*,\s*(?P<args>.*?)\)\s*;\s*(?://.*)?$')
_SKIP_CALL = re.compile(r'^\s*skipListAddName\(')
_LIST = re.compile(r'private\s+static\s+final\s+String\s+(SKIP_LIST_\w+)\s*=\s*"(\w+)"')
_OPT_IN = re.compile(r'private\s+static\s+(?:final\s+)?(?:String|boolean)\s+(FULL_ABILITIES_CHECK_SET_CODES|CHECK_ONLY_ABILITIES_TEXT)\s*=\s*([^;]+);')


def inventory(source: Path = SOURCE) -> dict:
    text = source.read_text(encoding="utf-8")
    lines = text.splitlines()
    disabled = []
    for index, line in enumerate(lines):
        match = _IGNORE.match(line)
        if not match:
            continue
        for follower in lines[index + 1:index + 4]:
            method = _METHOD.match(follower)
            if method:
                disabled.append({"method": method.group("name"),
                                 "reason": (match.group("reason") or "").strip() or "no reason given in source"})
                break
        else:
            raise SystemExit("@Ignore at line {} is not followed by a test method".format(index + 1))
    names = dict(_LIST.findall(text))
    skips: dict = {}
    for number, line in enumerate(lines, 1):
        if not _SKIP_CALL.match(line):
            continue
        match = _SKIP.match(line)
        if not match:
            raise SystemExit("unreadable skip-list entry at line {}: {}".format(number, line.strip()))
        list_name = names.get(match.group(1), match.group(1))
        skips.setdefault(list_name, []).append(" ".join(match.group("args").split()))
    opt_in = []
    for flag, default in _OPT_IN.findall(text):
        opt_in.append({"flag": flag, "default": default.strip(),
                       "effect": {"FULL_ABILITIES_CHECK_SET_CODES":
                                      "full ability-text comparison against MTGJSON runs only for the set codes "
                                      "in -Dxmage.tests.verifyCheckSetCodes; empty by default, so it is NOT_RUN",
                                  "CHECK_ONLY_ABILITIES_TEXT":
                                      "when true, suppresses every other check; false by default"}.get(flag, "")})
    return {
        "schema": SCHEMA,
        "source": str(source.relative_to(ROOT)),
        "disabled_tests": sorted(disabled, key=lambda d: d["method"]),
        "skip_lists": {name: sorted(entries) for name, entries in sorted(skips.items())},
        "skip_entry_counts": {name: len(entries) for name, entries in sorted(skips.items())},
        "opt_in_checks": sorted(opt_in, key=lambda o: o["flag"]),
        "claim": "Listed tests, skip-list entries and opt-in checks are NOT_RUN in a default Mage.Verify run; "
                 "a green Verify result covers only the executed remainder.",
    }


def render(doc: dict) -> str:
    return json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    current = render(inventory())
    if args.write:
        INVENTORY.write_text(current, encoding="utf-8")
        print("wrote " + str(INVENTORY.relative_to(ROOT)))
        return 0
    committed = INVENTORY.read_text(encoding="utf-8") if INVENTORY.is_file() else ""
    doc = json.loads(current)
    summary = "{} disabled test(s), {} skip-list entr(y/ies), {} opt-in check(s)".format(
        len(doc["disabled_tests"]), sum(doc["skip_entry_counts"].values()), len(doc["opt_in_checks"]))
    if committed != current:
        print("Mage.Verify coverage gaps changed without updating {}: {}".format(
            INVENTORY.relative_to(ROOT), summary))
        print("digest committed={} current={}".format(
            hashlib.sha256(committed.encode()).hexdigest()[:12], hashlib.sha256(current.encode()).hexdigest()[:12]))
        return 1
    print("Mage.Verify coverage gaps unchanged: " + summary)
    return 0


if __name__ == "__main__":
    sys.exit(main())
