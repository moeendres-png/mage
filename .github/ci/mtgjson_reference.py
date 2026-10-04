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
import datetime
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
        if names != [path.name.removesuffix(".zip")]:
            raise SystemExit("unexpected archive layout in {}: {}".format(path.name, names))
        with archive.open(names[0]) as member:
            head = member.read(1 << 16).decode("utf-8")
    match = re.search(r'"meta"\s*:\s*(\{[^{}]*\})', head)
    if not match:
        raise SystemExit("no meta object at the start of " + path.name)
    meta = json.loads(match.group(1))
    if not isinstance(meta.get("version"), str) or not isinstance(meta.get("date"), str):
        raise SystemExit("meta lacks version or date: {}".format(meta))
    datetime.date.fromisoformat(meta["date"])
    return {"version": meta["version"], "date": meta["date"]}


def cmd_pin(args) -> int:
    directory = Path(args.dir)
    meta = read_meta(directory / "AllPrintings.json.zip")
    if read_meta(directory / "AtomicCards.json.zip") != meta:
        raise ValueError("mixed MTGJSON reference epochs")
    files = {name: {"sha256": sha256(directory / name), "bytes": (directory / name).stat().st_size}
             for name in FILES}
    content_identity = hashlib.sha256(json.dumps(files, sort_keys=True).encode()).hexdigest()[:24]
    tag = "mtgjson-reference-" + re.sub(r"[^A-Za-z0-9._-]", "-", meta["version"]) + "-" + content_identity
    pin = {
        "schema": SCHEMA,
        "release": tag,
        "repository": args.repo,
        "files": files,
        "meta": meta,
    }
    validate_pin(pin)
    Path(args.out).write_text(json.dumps(pin, indent=2, sort_keys=True) + "\n")
    print(tag)
    return 0


def validate_pin(pin):
    if (not isinstance(pin, dict) or pin.get("schema") != SCHEMA
            or not isinstance(pin.get("files"), dict) or set(pin["files"]) != set(FILES)
            or not isinstance(pin.get("repository"), str)
            or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", pin["repository"])
            or not isinstance(pin.get("release"), str)
            or not re.fullmatch(r"mtgjson-reference-[A-Za-z0-9_.-]+", pin["release"])
            or not isinstance(pin.get("meta"), dict)
            or set(pin["meta"]) != {"version", "date"}
            or not all(isinstance(v, str) and v for v in pin["meta"].values())):
        raise ValueError("malformed MTGJSON pin")
    datetime.date.fromisoformat(pin["meta"]["date"])
    for expected in pin["files"].values():
        if (not isinstance(expected, dict) or set(expected) != {"sha256", "bytes"}
                or not isinstance(expected["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", expected["sha256"])
                or type(expected["bytes"]) is not int or expected["bytes"] <= 0):
            raise ValueError("malformed pinned file identity")


def verify_file(path, expected, meta):
    if path.is_symlink() or not path.is_file():
        raise ValueError("missing/non-regular reference: " + path.name)
    if sha256(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
        raise ValueError("reference bytes differ from pin: " + path.name)
    if read_meta(path) != meta:
        raise ValueError("reference meta differs from pin: " + path.name)


def cmd_fetch(args) -> int:
    receipt_path = Path(args.receipt)
    if receipt_path.is_symlink():
        raise ValueError("non-regular receipt destination")
    # A failed repeated fetch must not leave a historical PASS receipt behind.
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps({"schema": SCHEMA + "#receipt", "status": "NOT_RUN"}) + "\n")
    try:
        pin_path = Path(args.pin)
        pin = json.loads(pin_path.read_text())
        validate_pin(pin)
        directory = Path(args.dir)
        directory.mkdir(parents=True, exist_ok=True)
        for name, expected in sorted(pin["files"].items()):
            target = directory / name
            if target.is_symlink():
                raise ValueError("non-regular reference destination")
            # Exact content-addressed cache hit is reuse, never unverified trust.
            if not target.is_file() or sha256(target) != expected["sha256"] or target.stat().st_size != expected["bytes"]:
                url = RELEASE_URL.format(repo=pin["repository"], tag=pin["release"], name=name)
                with urllib.request.urlopen(url, timeout=600) as response, target.open("wb") as out:
                    while block := response.read(1 << 20):
                        out.write(block)
            verify_file(target, expected, pin["meta"])
        receipt = {"schema": SCHEMA + "#receipt", "status": "INPUT_BOUND",
                   "release": pin["release"], "repository": pin["repository"],
                   "files": pin["files"], "meta": pin["meta"], "pin_sha256": sha256(pin_path),
                   "qualification_credit": False}
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print("MTGJSON reference bound: {} (meta {} / {})".format(pin["release"], pin["meta"]["version"], pin["meta"]["date"]))
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, SystemExit) as exc:
        receipt_path.write_text(json.dumps({"schema": SCHEMA + "#receipt", "status": "FAIL",
                                          "error": str(exc), "qualification_credit": False}) + "\n")
        print("MTGJSON_REFERENCE = FAIL " + json.dumps(str(exc), ensure_ascii=True), file=sys.stderr)
        return 1


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
