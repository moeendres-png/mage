#!/usr/bin/env python3
"""C14 (commander-playtest-lab#495): pinned MTGJSON reference for Mage.Verify.

``pin``   (refresh only) reads freshly downloaded MTGJSON files and writes the
          pin: each file's SHA-256 and size, AllPrintings' meta version and
          date, and the release that holds the immutable copies.
``fetch`` (qualification) downloads exactly the pinned release assets, refuses
          any byte or size difference, and writes a receipt naming the reference
          the run verified against. It never touches mtgjson.com.

Standard library only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
import zipfile
from pathlib import Path

SCHEMA = "mage.verify.mtgjson-reference/1"
FILES = ("AllPrintings.json.zip", "AtomicCards.json.zip")
RELEASE_URL = "https://github.com/{repo}/releases/download/{tag}/{name}"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_meta(path: Path) -> dict:
    """AllPrintings' meta object, which MTGJSON writes before the data."""
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != 1:
            raise SystemExit("unexpected archive layout in {}: {}".format(path.name, names))
        with archive.open(names[0]) as member:
            head = member.read(1 << 16).decode("utf-8", "replace")
    match = re.search(r'"meta"\s*:\s*(\{[^{}]*\})', head)
    if not match:
        raise SystemExit("no meta object at the start of " + path.name)
    meta = json.loads(match.group(1))
    if not meta.get("version") or not meta.get("date"):
        raise SystemExit("meta lacks version or date: {}".format(meta))
    return {"version": meta["version"], "date": meta["date"]}


def cmd_pin(args) -> int:
    directory = Path(args.dir)
    meta = read_meta(directory / "AllPrintings.json.zip")
    tag = "mtgjson-reference-" + re.sub(r"[^A-Za-z0-9._-]", "-", meta["version"])
    pin = {
        "schema": SCHEMA,
        "release": tag,
        "repository": args.repo,
        "files": {name: {"sha256": sha256(directory / name), "bytes": (directory / name).stat().st_size}
                  for name in FILES},
        "meta": meta,
    }
    Path(args.out).write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n")
    print(tag)
    return 0


def cmd_fetch(args) -> int:
    pin = json.loads(Path(args.pin).read_text())
    if pin.get("schema") != SCHEMA or set(pin.get("files") or {}) != set(FILES):
        raise SystemExit("malformed pin " + args.pin)
    directory = Path(args.dir)
    directory.mkdir(parents=True, exist_ok=True)
    for name, expected in sorted(pin["files"].items()):
        target = directory / name
        url = RELEASE_URL.format(repo=pin["repository"], tag=pin["release"], name=name)
        with urllib.request.urlopen(url, timeout=600) as response, target.open("wb") as out:
            while True:
                block = response.read(1 << 20)
                if not block:
                    break
                out.write(block)
        actual = sha256(target)
        if actual != expected["sha256"] or target.stat().st_size != expected["bytes"]:
            raise SystemExit("{} does not match the pin: sha256 {} ({} bytes), pinned {} ({} bytes)".format(
                name, actual, target.stat().st_size, expected["sha256"], expected["bytes"]))
    if read_meta(directory / "AllPrintings.json.zip") != pin["meta"]:
        raise SystemExit("AllPrintings meta does not match the pin")
    receipt = {"schema": SCHEMA + "#receipt", "release": pin["release"], "repository": pin["repository"],
               "files": pin["files"], "meta": pin["meta"], "pin_sha256": sha256(Path(args.pin))}
    Path(args.receipt).parent.mkdir(parents=True, exist_ok=True)
    Path(args.receipt).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print("MTGJSON reference bound: {} (meta {} / {})".format(pin["release"], pin["meta"]["version"], pin["meta"]["date"]))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("pin")
    p.add_argument("--dir", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--out", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--pin", required=True)
    f.add_argument("--dir", required=True)
    f.add_argument("--receipt", required=True)
    args = parser.parse_args(argv)
    return cmd_pin(args) if args.command == "pin" else cmd_fetch(args)


if __name__ == "__main__":
    sys.exit(main())
