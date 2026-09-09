#!/usr/bin/env python3
"""Survey template-113 STATE_ONLY paths for clean production fixtures.

For every template-113 path in the owned C manifest, inspects each
provenance card script at FORGE_PIN and reports, per (path, card):
  - parent SVar chain (SVar name at provenance line, DB type, SubAbility pointer)
  - root record kind/fixture class (ETB_SELF / PHASE / CAST / COMBAT / OTHER)
  - structural screen verdict (decision/target/RNG/hidden fields)

Structural screen operates on parsed SVar/A/T record FIELDS (prose
descriptions excluded). Findings are descriptive; selection happens
separately. Deterministic output.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"

TEXT_FIELDS = {
    "Description", "SpellDescription", "TriggerDescription", "StackDescription",
    "TgtPrompt", "SelectPrompt", "ChoiceTitle", "AILogic", "PrecostDesc",
    "CostDesc", "ValidTgtsDesc", "ValidDescription", "ChangeTypeDesc",
}
# Fields that force a decision/target/RNG/hidden verdict when present in a
# NON-text field of any SVar/A/T record of the script.
DECISION_FIELDS = {
    "Choices", "Optional", "OptionalDecider", "UnlessCost", "UnlessPayer",
    "TargetMin", "TargetMax", "RepeatSubAbility", "RepeatPlayers",
    "ChooseNumberSubAbility", "BidSubAbility", "VoteSubAbility",
    "CharmNum", "MinCharmNum", "ChoiceZone", "RememberChosen",
}
TARGET_FIELDS = {"ValidTgts"}
RNG_FIELDS = {"Coin", "Dice", "Flip", "Random"}
HIDDEN_FIELDS = {"Hidden", "Reveal", "RememberRevealed", "NoPeek",
                 "DigNum", "Dig", "RevealNumber", "RememberMilled"}
SEARCH_FIELDS = {"ChangeType"}  # only meaningful combined with Origin$ Library
CHOICE_MODES = {"TgtChoose"}
VALUE_RNG_RE = re.compile(r"\b(Random|CoinFlip|DiceRoll)\b")


def parse_fields(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in body.split("|"):
        part = part.strip()
        if "$" not in part:
            continue
        k, v = part.split("$", 1)
        out[k.strip()] = v.strip()
    return out


def split_records(text: str):
    """Yield (kind, name, fields, line_no, raw) for SVar/A/T lines."""
    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if s.startswith("SVar:"):
            rest = s[5:]
            if ":" not in rest:
                continue
            name, val = (x.strip() for x in rest.split(":", 1))
            yield ("SVAR", name, parse_fields(val), n, val)
        elif s[:2] in ("A:", "T:") and len(s) > 2:
            kind = {"A": "ABILITY", "T": "TRIGGER"}[s[0]]
            yield (kind, "", parse_fields(s[2:]), n, s[2:])


def screen_script(text: str) -> dict:
    hits: dict[str, list] = collections.defaultdict(list)
    for kind, name, flds, n, _ in split_records(text):
        for k, v in flds.items():
            if k in TEXT_FIELDS:
                continue
            if k in DECISION_FIELDS:
                hits["DECISION"].append(f"{kind}:{name}:{k}@{n}")
            if k in TARGET_FIELDS:
                hits["TARGET"].append(f"{kind}:{name}:{k}@{n}")
            if k == "Mode" and v in CHOICE_MODES:
                hits["DECISION"].append(f"{kind}:{name}:Mode={v}@{n}")
            if k in RNG_FIELDS or VALUE_RNG_RE.search(v or ""):
                hits["RNG"].append(f"{kind}:{name}:{k}@{n}")
            if k in HIDDEN_FIELDS:
                hits["HIDDEN"].append(f"{kind}:{name}:{k}@{n}")
            if k == "ChangeType" and flds.get("Origin") == "Library":
                hits["SEARCH_SHUFFLE"].append(f"{kind}:{name}:{k}@{n}")
    return {k: sorted(v) for k, v in hits.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--forge-git", type=Path, required=True,
                    help="Forge git repo dir containing FORGE_PIN objects (read via git show; no checkout needed)")
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    typ = subprocess.check_output(
        ["git", "-C", str(args.forge_git), "cat-file", "-t", FORGE_PIN], text=True
    ).strip()
    assert typ == "commit", f"Forge pin object missing {FORGE_PIN}"

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    assert manifest["forge_pin"] == FORGE_PIN
    cache: dict[str, str] = {}

    def script(rel: str) -> str:
        if rel not in cache:
            r = subprocess.run(
                ["git", "-C", str(args.forge_git), "show", f"{FORGE_PIN}:{rel}"],
                capture_output=True, text=True)
            cache[rel] = r.stdout if r.returncode == 0 else ""
        return cache[rel]

    report = []
    for row in manifest["paths"]:
        if row["scenario_group_id"] != "ws33-template-113":
            continue
        want_sub = row["semantic_selector_profile"]["selectors"].get("SubAbility")
        for prov in row["source_provenance"]:
            rel = prov["forge_source_path"]
            txt = script(rel)
            if not txt:
                report.append({"path": row["effective_v2_path_id"], "card": rel,
                               "verdict": "CARD_SOURCE_MISSING"})
                continue
            svars: dict[str, dict] = {}
            roots = []
            for kind, name, flds, n, _ in split_records(txt):
                if kind == "SVAR":
                    svars[name] = {"fields": flds, "line": n}
                else:
                    roots.append({"kind": kind, "fields": flds, "line": n})
            decl = svars.get(prov["source_token"])
            if decl is None or decl["line"] != prov["source_line"]:
                # Provenance token is a generic DB marker; resolve the actual
                # parent SVar below via SubAbility back-pointers instead.
                decl = None
            # Find candidate parent SVars: any SVar whose SubAbility == want_sub
            # or which IS want_sub's own definition context.
            parents = [
                {"svar": nm, "line": d["line"], "db_type": (d["fields"].get("DB", "?") if False else "?"),
                 "fields": d["fields"]}
                for nm, d in svars.items()
                if d["fields"].get("SubAbility") == want_sub
            ]
            # Root fixture classes present in script
            fixtures = []
            for r in roots:
                f = r["fields"]
                if r["kind"] == "TRIGGER" and f.get("Mode") == "ChangesZone" \
                        and f.get("Destination") == "Battlefield" \
                        and "Card.Self" in f.get("ValidCard", "") and "Execute" in f:
                    fixtures.append(f"ETB_SELF:{f.get('Execute')}")
                elif r["kind"] == "TRIGGER" and f.get("Mode") == "Phase":
                    fixtures.append(f"PHASE:{f.get('Phase')}:{f.get('Execute', '')}")
                elif r["kind"] == "TRIGGER":
                    fixtures.append(f"OTHER_TRIGGER:{f.get('Mode')}:{f.get('Execute', '')}")
                elif r["kind"] == "ABILITY":
                    fixtures.append("ABILITY_ACTIVATED_OR_SPELL")
            report.append({
                "path": row["effective_v2_path_id"],
                "selectors": row["semantic_selector_profile"]["selectors"],
                "card": rel,
                "oracle": prov["oracle_identity"],
                "provenance_line": prov["source_line"],
                "candidate_parents": [
                    {"svar": p["svar"], "line": p["line"],
                     "record_head": " ".join(
                         f'{k}${v}' for k, v in list(p["fields"].items())[:3])}
                    for p in parents
                ],
                "fixtures": sorted(set(fixtures)),
                "screen": screen_script(txt),
                "verdict": "NEEDS_SELECTION",
            })
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps({"schema": "commander-simulator-next.ws33-c-t113-survey.v1",
                    "forge_pin": FORGE_PIN, "rows": report},
                   sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n",
        encoding="utf-8")
    by_card: dict[str, set] = collections.defaultdict(set)
    for r in report:
        by_card[r["card"]].add(r["path"][:14])
    print(json.dumps({"SURVEY_ROWS": len(report), "CARDS": len(by_card)}, sort_keys=True))


if __name__ == "__main__":
    main()
