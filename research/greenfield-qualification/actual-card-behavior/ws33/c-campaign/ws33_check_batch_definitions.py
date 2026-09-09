#!/usr/bin/env python3
"""Verify WS33-C batch definitions against immutable inputs (deterministic).

For every execution in the definitions file, asserts:
  - each link path is in the owned C manifest, currently UNKNOWN, template-113,
    STATE_ONLY dimensions, AbilitySub target, no overlap with evidenced paths;
  - provenance (source_path/oracle/line) matches the manifest row;
  - card script at FORGE_PIN (via git show, no checkout needed) contains the
    parent SVar with the declared DB type and SubAbility pointer, and the
    child SVar with the declared DB type;
  - full-script structural screen is clean (no decision/target/RNG/hidden/
    search-shuffle fields outside prose text).

Emits the canonical batch digest. Exit nonzero on any violation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ws33_survey_t113_fixtures import screen_script, FORGE_PIN  # noqa: E402

DB_HEAD_RE = re.compile(r"DB\$\s*([A-Za-z]+)")


def canon(o) -> bytes:
    return (json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n").encode()


def fail(msg: str):
    raise SystemExit(f"WS33_C_BATCH_CHECK=FAIL {msg}")


def parse_svars(text: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s.startswith("SVar:"):
            continue
        rest = s[5:]
        if ":" not in rest:
            continue
        name, val = (x.strip() for x in rest.split(":", 1))
        flds: dict[str, str] = {}
        for part in val.split("|"):
            part = part.strip()
            if "$" in part:
                k, v = part.split("$", 1)
                flds[k.strip()] = v.strip()
        head = DB_HEAD_RE.match(val)
        out[name] = {"fields": flds, "line": n,
                     "db_type": head.group(1) if head else None, "raw": val}
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--definitions", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--coverage", type=Path, required=True)
    ap.add_argument("--partition", type=Path, required=True)
    ap.add_argument("--forge-git", type=Path, required=True)
    ap.add_argument("--allow-rewitness", nargs="*", default=[],
                    help="Explicitly declared already-evidenced path IDs re-witnessed to upgrade evidence (never silent).")
    args = ap.parse_args()

    defs = json.loads(args.definitions.read_text(encoding="utf-8"))
    assert defs["forge_pin"] == FORGE_PIN
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    coverage = json.loads(args.coverage.read_text(encoding="utf-8"))
    partition = json.loads(args.partition.read_text(encoding="utf-8"))
    owned = {r["effective_v2_path_id"]: r for r in manifest["paths"]}
    cov = {r["effective_v2_path_id"]: r["status"] for r in coverage["paths"]}
    evidenced = {e["effective_v2_path_id"] for e in partition["evidenced"]}

    typ = subprocess.check_output(
        ["git", "-C", str(args.forge_git), "cat-file", "-t", FORGE_PIN], text=True).strip()
    if typ != "commit":
        fail(f"Forge pin object missing {FORGE_PIN}")
    cache: dict[str, str] = {}

    def script(rel: str) -> str:
        if rel not in cache:
            r = subprocess.run(
                ["git", "-C", str(args.forge_git), "show", f"{FORGE_PIN}:{rel}"],
                capture_output=True, text=True)
            if r.returncode != 0:
                fail(f"card source missing at pin: {rel}")
            cache[rel] = r.stdout
        return cache[rel]

    seen_paths: set[str] = set()
    for ex in defs["executions"]:
        txt = script(ex["source_path"])
        svars = parse_svars(txt)
        hits = screen_script(txt)
        if hits:
            fail(f"{ex['execution_id']}: structural screen hits {hits}")
        for link in ex["links"]:
            pid = link["path_id"]
            if pid in seen_paths:
                fail(f"duplicate path in batch: {pid}")
            seen_paths.add(pid)
            row = owned.get(pid)
            if row is None:
                fail(f"path not in owned manifest: {pid}")
            if not (row["scenario_group_id"] == "ws33-template-113"
                    and row["implementation_target"] == "forge.game.spellability.AbilitySub"):
                fail(f"path outside capped scope: {pid}")
            if row["requires_decision"] or row["requires_hidden"] \
                    or row["requires_replay"] or row["requires_rng"]:
                fail(f"path not STATE_ONLY: {pid}")
            if cov.get(pid) != "UNKNOWN":
                fail(f"path not currently UNKNOWN: {pid}")
            if pid in evidenced and pid not in set(args.allow_rewitness):
                fail(f"path already evidenced (not declared re-witness): {pid}")
            if pid in evidenced:
                print(json.dumps({"REWITNESS_DECLARED": pid}, sort_keys=True))
            prov = [q for q in row["source_provenance"]
                    if q["forge_source_path"] == ex["source_path"]
                    and q["oracle_identity"] == ex["oracle_identity"]]
            if not prov:
                fail(f"provenance mismatch {pid} {ex['source_path']}")
            if row["semantic_selector_profile"]["selectors"].get("SubAbility") != link["child_sub"]:
                fail(f"selector/child_sub mismatch {pid}")
            parent = svars.get(link["parent_svar"])
            if parent is None:
                fail(f"parent SVar missing {ex['execution_id']}.{link['parent_svar']}")
            if parent["line"] != link["parent_line"]:
                fail(f"parent line mismatch {link['parent_svar']}")
            if parent["db_type"] != link["parent_api"]:
                # DB$ head token maps 1:1 to ApiType names on the executed set
                fail(f"parent api mismatch {link['parent_svar']}: "
                     f"script={parent['db_type']} decl={link['parent_api']}")
            if parent["fields"].get("SubAbility") != link["child_sub"]:
                fail(f"SubAbility pointer mismatch {link['parent_svar']}")
            child = svars.get(link["child_sub"])
            if child is None or child["db_type"] != link["child_api"]:
                fail(f"child SVar/api mismatch {link['child_sub']}")
    digest = hashlib.sha256(canon(defs)).hexdigest()
    print(json.dumps({"WS33_C_BATCH_CHECK": "PASS",
                      "batch": defs["batch_id"],
                      "executions": len(defs["executions"]),
                      "paths": len(seen_paths),
                      "BATCH_DIGEST": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
