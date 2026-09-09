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


def parse_svars(text: str) -> dict[str, list[dict]]:
    # SVar identity is (name, line): double-faced cards repeat names.
    out: dict[str, list[dict]] = {}
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
        out.setdefault(name, []).append(
            {"fields": flds, "line": n,
             "db_type": head.group(1) if head else None, "raw": val})
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
    api_names: set[str] = set()

    def api_allowlist() -> set[str]:
        nonlocal api_names
        if not api_names:
            r = subprocess.run(
                ["git", "-C", str(args.forge_git), "show",
                 f"{FORGE_PIN}:forge-game/src/main/java/forge/game/ability/ApiType.java"],
                capture_output=True, text=True)
            if r.returncode != 0:
                fail("ApiType.java missing at pin")
            api_names = set(re.findall(r"^    (\w+) \(", r.stdout, re.M))
            if not api_names:
                fail("ApiType allowlist empty")
        return api_names
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
    apis = api_allowlist()
    for ex in defs["executions"]:
        for s in ex.get("setup", []):
            if s.get("zone") not in ("Battlefield", "Hand", "Library"):
                fail(f"bad setup zone {ex['execution_id']}")
            if s.get("who") not in ("actor", "opponent"):
                fail(f"bad setup owner {ex['execution_id']}")
            if not isinstance(s.get("count"), int) or s["count"] < 1:
                fail(f"bad setup count {ex['execution_id']}")
            if s.get("via", "place") not in ("place", "move"):
                fail(f"bad setup via {ex['execution_id']}")
            if s.get("via") == "move" and s.get("zone") != "Battlefield":
                fail(f"via=move requires Battlefield zone {ex['execution_id']}")
        declared_cards = {ex["card_name"]}
        declared_cards.update(s.get("card_name", "") for s in ex.get("setup", []))
        if ex["fixture"].get("entering_card"):
            declared_cards.add(ex["fixture"]["entering_card"])
        for a in ex.get("assertions", []):
            if a.get("name"):
                declared_cards.add(a["name"])
            if a.get("card") and a["card"] != "source":
                declared_cards.add(a["card"])
        for c in ex.get("expected_consultations", []):
            if not c.get("site") or not isinstance(c.get("options"), int):
                fail(f"bad consultation declaration {ex['execution_id']}")
            if c["options"] != 1:
                fail(f"only singleton consultations supported {ex['execution_id']}")
            if not c.get("selected_card") or c["selected_card"] not in declared_cards:
                fail(f"consultation selected_card not in declared universe {ex['execution_id']}")
            if not any((a.get("card") == c["selected_card"] or
                        (a.get("card") == "source" and ex["card_name"] == c["selected_card"]) or
                        a.get("name") == c["selected_card"])
                       for a in ex.get("assertions", [])):
                fail(f"consultation selected_card has no covering assertion {ex['execution_id']}")
        if ex["fixture"]["kind"] == "ETB_OTHER_ENTER" and not ex["fixture"].get("entering_card"):
            fail(f"ETB_OTHER_ENTER without entering_card {ex['execution_id']}")
        txt = script(ex["source_path"])
        screen_hits = screen_script(txt)
        if screen_hits:
            fail(f"{ex['execution_id']}: structural screen hits {screen_hits}")
        svars = parse_svars(txt)
        for link in ex["links"]:
            pid = link["path_id"]
            if pid in seen_paths and not ex.get("allow_shared_paths", False):
                fail(f"duplicate path in batch (not declared shared): {pid}")
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
            if row["semantic_selector_profile"]["selectors"].get("SubAbility") != link["child_sub"] \
                    and not (link.get("terminal", False) and "SubAbility" not in
                             row["semantic_selector_profile"]["selectors"]):
                fail(f"selector/child_sub mismatch {pid}")
            if link["parent_api"] not in apis or link["child_api"] not in apis:
                fail(f"api not in pin ApiType allowlist {pid}")
            parent = next(
                (d for d in svars.get(link["parent_svar"], [])
                 if d["line"] == link["parent_line"]), None)
            if parent is None:
                fail(f"parent SVar missing {ex['execution_id']}.{link['parent_svar']}"
                     f"@{link['parent_line']}")
            if parent["db_type"] != link["parent_api"]:
                fail(f"parent api mismatch {link['parent_svar']}: "
                     f"script={parent['db_type']} decl={link['parent_api']}")
            if link.get("terminal", False):
                if link["child_sub"] != "TERMINAL" or link["child_api"] != link["parent_api"]:
                    fail(f"terminal link shape mismatch {pid}")
                if parent["fields"].get("SubAbility") is not None:
                    fail(f"terminal parent has SubAbility pointer {pid}")
                continue
            if parent["fields"].get("SubAbility") != link["child_sub"]:
                fail(f"SubAbility pointer mismatch {link['parent_svar']}")
            child = next(
                (d for d in svars.get(link["child_sub"], [])
                 if d["db_type"] == link["child_api"]), None)
            if child is None:
                fail(f"child SVar/api mismatch {link['child_sub']}")
    digest = hashlib.sha256(canon(defs)).hexdigest()
    print(json.dumps({"WS33_C_BATCH_CHECK": "PASS",
                      "batch": defs["batch_id"],
                      "executions": len(defs["executions"]),
                      "paths": len(seen_paths),
                      "BATCH_DIGEST": digest}, sort_keys=True))


if __name__ == "__main__":
    main()
