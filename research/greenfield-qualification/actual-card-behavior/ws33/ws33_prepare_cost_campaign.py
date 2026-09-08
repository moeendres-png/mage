#!/usr/bin/env python3
"""Prepare the WS33B Cost campaign (402 canonical paths).

Reads the canonical 4188-row integrated closure ledger (never the superseded
4276-world registry), selects exactly the WS33B forge.game.cost.Cost UNKNOWN
set, classifies each path by cost-expression shape, picks a representative
(card, cost expression) verified against pinned Forge, plans deterministic
mana supply and fixture fodder, and emits a case TSV plus a plan JSON.

Cost expressions are parsed compositionally into parts (mana, tap,
sacrifice, exile, discard, counters, life, return, unattach, draw, tapXType,
implicit spell costs). Shapes needing not-yet-built fixture infrastructure
are emitted with explicit UNSUPPORTED_* recipe tags so the test fails closed.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

COST_TARGET = "forge.game.cost.Cost"
BASIC_FOR_COLOR = {"W": "Plains", "U": "Island", "B": "Swamp", "R": "Mountain", "G": "Forest"}
COLOR_TOKENS = set("WUBRG")


def b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33_COST_PREPARE=FAIL " + message)


def parse_mana_tokens(cost: str) -> tuple[int, Counter, int]:
    """Return (generic, colors Counter, x_count) for a mana-ish cost string."""
    generic = 0
    colors: Counter = Counter()
    x_count = 0
    for token in cost.split():
        if token == "X":
            x_count += 1
        elif token.isdigit():
            generic += int(token)
        elif set(token) <= COLOR_TOKENS and token:
            for ch in token:
                colors[ch] += 1
        elif re.fullmatch(r"2/[WUBRG]", token):
            colors[token.split("/")[1]] += 1
            generic += 0
        elif token in ("T",):
            pass
        else:
            return (-1, Counter(), -1)
    return (generic, colors, x_count)


def plan_supply(generic: int, colors: Counter, x_value: int) -> dict:
    """Deterministic mana supply plan: Sol Rings cover generic+X, basics cover colors."""
    total_generic = generic + x_value
    rings = (total_generic + 1) // 2 if total_generic > 0 else 0
    lands = []
    for color, count in sorted(colors.items()):
        lands.extend([BASIC_FOR_COLOR[color]] * count)
    return {"sol_rings": rings, "lands": lands, "x_value": x_value}


def read_card_text(card_path: Path) -> tuple[str, list[str]]:
    lines = card_path.read_text(encoding="utf-8").splitlines()
    name = next((line[5:].strip() for line in lines if line.startswith("Name:")), "")
    return name, lines


def mana_cost_of(lines: list[str]) -> str:
    for line in lines:
        if line.startswith("ManaCost:"):
            return line.split(":", 1)[1].strip()
    return ""


def has_activated_with_cost(lines: list[str], line_no: int) -> bool:
    if line_no < 1 or line_no > len(lines):
        return False
    text = lines[line_no - 1].strip()
    fields = [field.strip() for field in text.split("|")]
    return bool(fields) and fields[0].startswith("A:")


def assign_recipe(card_name: str, directive: str, token: str, expr: str,
                  lines: list[str]) -> tuple[str, dict]:
    """Return (recipe, params). Params are fixture inputs, never engine outputs."""
    if directive == "ABILITY" and token == "implicit-spell-cost":
        cost = mana_cost_of(lines)
        if not cost or cost == "no cost":
            return "CAST_NO_COST", {}
        generic, colors, x_count = parse_mana_tokens(cost)
        if generic < 0:
            return "UNSUPPORTED_COST_MANA", {"cost": cost}
        x_value = 2 if x_count else 0
        return "CAST_SPELL", {"cost": cost, "supply": plan_supply(generic, colors, x_value)}
    if directive == "MANA_COST":
        if expr in ("no cost",):
            return "CAST_NO_COST", {}
        generic, colors, x_count = parse_mana_tokens(expr)
        if generic < 0:
            return "UNSUPPORTED_COST_MANA", {"cost": expr}
        x_value = 2 if x_count else 0
        return "CAST_SPELL", {"cost": expr, "supply": plan_supply(generic, colors, x_value)}
    if token == "Cost$":
        parts = expr.split()
        # Pure tap.
        if parts == ["T"]:
            return "PAY_TAP", {}
        # Pure generic mana.
        if all(p.isdigit() for p in parts):
            generic = sum(int(p) for p in parts)
            return "PAY_MANA", {"cost": expr, "supply": plan_supply(generic, Counter(), 0)}
        # Mana + tap mixtures without special parts.
        simple = [p for p in parts if p not in ("T",)]
        if simple and all(p.isdigit() or (set(p) <= COLOR_TOKENS and p) or re.fullmatch(r"2/[WUBRG]", p) for p in simple):
            generic = sum(int(p) for p in simple if p.isdigit())
            colors = Counter()
            for p in simple:
                if set(p) <= COLOR_TOKENS and p and not p.isdigit():
                    for ch in p:
                        colors[ch] += 1
                elif re.fullmatch(r"2/[WUBRG]", p):
                    colors[p.split("/")[1]] += 1
            return "PAY_MANA_TAP", {"cost": expr, "supply": plan_supply(generic, colors, 0)}
        # X costs.
        if "X" in parts and all(p in ("X", "T") or p.isdigit() or (set(p) <= COLOR_TOKENS and p) for p in parts):
            generic = sum(int(p) for p in parts if p.isdigit())
            colors = Counter()
            for p in parts:
                if set(p) <= COLOR_TOKENS and p and not p.isdigit() and p != "X":
                    for ch in p:
                        colors[ch] += 1
            x_count = sum(1 for p in parts if p == "X")
            x_value = 2 * x_count
            supply = plan_supply(generic, colors, x_value)
            if "T" in parts:
                return "PAY_X_MANA_TAP", {"cost": expr, "supply": supply}
            return "PAY_X_MANA", {"cost": expr, "supply": supply}
        # Sacrifice-led shapes (single Sac part, optional mana/tap).
        sac = [p for p in parts if p.startswith("Sac<")]
        exotic = [p for p in parts if p.startswith(("Choose", "Choice", "Reveal", "Mill<", "Clash", "Flip"))]
        if exotic:
            return "UNSUPPORTED_COST_PART", {"expression": expr}
        rest = [p for p in parts if not p.startswith("Sac<")]
        if len(sac) == 1 and all(p in ("T",) or p.isdigit() or (set(p) <= COLOR_TOKENS and p) for p in rest):
            generic = sum(int(p) for p in rest if p.isdigit())
            colors = Counter()
            for p in rest:
                if set(p) <= COLOR_TOKENS and p and not p.isdigit():
                    for ch in p:
                        colors[ch] += 1
            fodder = sac_fodder(sac[0])
            if fodder is None:
                return "UNSUPPORTED_COST_SAC", {"expression": expr}
            return "PAY_SAC", {"cost": expr, "supply": plan_supply(generic, colors, 0),
                               "tap": "T" in rest, "fodder": fodder}
        # Exile-led shapes.
        exile = [p for p in parts if p.startswith(("Exile<", "ExileFromGrave<", "ExileAnyGrave<"))]
        if len(exile) == 1 and all(p in ("T",) or p.isdigit() or (set(p) <= COLOR_TOKENS and p) for p in
                                   [x for x in parts if x not in exile]):
            rest2 = [x for x in parts if x not in exile]
            generic = sum(int(p) for p in rest2 if p.isdigit())
            colors = Counter()
            for p in rest2:
                if set(p) <= COLOR_TOKENS and p and not p.isdigit():
                    for ch in p:
                        colors[ch] += 1
            zone = exile_zone(exile[0])
            if zone is None:
                return "UNSUPPORTED_COST_EXILE", {"expression": expr}
            return "PAY_EXILE", {"cost": expr, "supply": plan_supply(generic, colors, 0),
                                 "tap": "T" in rest2, "zone": zone}
        # Discard-led shapes.
        discard = [p for p in parts if p.startswith("Discard<")]
        if len(discard) == 1 and all(p in ("T",) or p.isdigit() or (set(p) <= COLOR_TOKENS and p) for p in
                                     [x for x in parts if x not in discard]):
            rest3 = [x for x in parts if x not in discard]
            generic = sum(int(p) for p in rest3 if p.isdigit())
            colors = Counter()
            for p in rest3:
                if set(p) <= COLOR_TOKENS and p and not p.isdigit():
                    for ch in p:
                        colors[ch] += 1
            return "PAY_DISCARD", {"cost": expr, "supply": plan_supply(generic, colors, 0),
                                   "tap": "T" in rest3}
        # Counter-led shapes.
        counters = [p for p in parts if p.startswith(("AddCounter<", "SubCounter<"))]
        if counters and all(p in ("T",) or p.isdigit() or (set(p) <= COLOR_TOKENS and p)
                            or p.startswith(("AddCounter<", "SubCounter<")) for p in parts):
            rest4 = [x for x in parts if x not in counters]
            generic = sum(int(p) for p in rest4 if p.isdigit())
            colors = Counter()
            for p in rest4:
                if set(p) <= COLOR_TOKENS and p and not p.isdigit():
                    for ch in p:
                        colors[ch] += 1
            return "PAY_COUNTERS", {"cost": expr, "supply": plan_supply(generic, colors, 0),
                                    "tap": "T" in rest4, "counters": counters}
        # Life-led shapes.
        if any(p.startswith("PayLife<") for p in parts):
            rest5 = [x for x in parts if not x.startswith("PayLife<")]
            if all(p in ("T",) or p.isdigit() or (set(p) <= COLOR_TOKENS and p) for p in rest5):
                generic = sum(int(p) for p in rest5 if p.isdigit())
                colors = Counter()
                for p in rest5:
                    if set(p) <= COLOR_TOKENS and p and not p.isdigit():
                        for ch in p:
                            colors[ch] += 1
                return "PAY_LIFE", {"cost": expr, "supply": plan_supply(generic, colors, 0),
                                    "tap": "T" in rest5}
        # Return-led shapes.
        if any(p.startswith("Return<") for p in parts):
            rest6 = [x for x in parts if not x.startswith("Return<")]
            if all(p in ("T",) or p.isdigit() or (set(p) <= COLOR_TOKENS and p) for p in rest6):
                generic = sum(int(p) for p in rest6 if p.isdigit())
                colors = Counter()
                for p in rest6:
                    if set(p) <= COLOR_TOKENS and p and not p.isdigit():
                        for ch in p:
                            colors[ch] += 1
                return "PAY_RETURN", {"cost": expr, "supply": plan_supply(generic, colors, 0),
                                      "tap": "T" in rest6}
        # tapXType shapes.
        tapx = [p for p in parts if p.startswith("tapXType<")]
        if len(tapx) == 1 and len(parts) == 1:
            inner = tapx[0][len("tapXType<"):-1]
            count, _, _type = inner.partition("/")
            try:
                need = int(count)
            except ValueError:
                return "UNSUPPORTED_COST_PART", {"expression": expr}
            return "PAY_TAPXTYPE", {"cost": expr, "type": _type.strip(), "need": need}
        return "UNSUPPORTED_COST_PART", {"expression": expr}
    return "UNSUPPORTED_COST_DIRECTIVE", {"directive": directive, "token": token}


def sac_fodder(part: str) -> dict | None:
    """Map a Sac<...> part to deterministic fodder, or None if exotic."""
    inner = part[len("Sac<"):-1] if part.endswith(">") else None
    if inner is None:
        return None
    count, _, valid = inner.partition("/")
    try:
        need = int(count)
    except ValueError:
        return None
    valid = valid.split("/")[0]
    if valid in ("CARDNAME", "Creature", "Creature.Other", "another creature"):
        return {"card": "Runeclaw Bear", "count": need, "controller": "ACTOR"}
    if valid == "Land" or valid == "land":
        return {"card": "Island", "count": need, "controller": "ACTOR"}
    if valid == "Artifact":
        return {"card": "Sol Ring", "count": need, "controller": "ACTOR"}
    if "Spirit" in valid:
        return None
    if "Legendary" in valid:
        return None
    if "Green" in valid or "White" in valid or "Blue" in valid:
        return {"card": "Runeclaw Bear", "count": need, "controller": "ACTOR"}
    if valid in ("Creature.Green", "Creature.White", "Creature.Blue"):
        return {"card": "Runeclaw Bear", "count": need, "controller": "ACTOR"}
    return None


def exile_zone(part: str) -> str | None:
    if part.startswith("Exile<"):
        return "HAND"
    if part.startswith("ExileFromGrave<"):
        return "GRAVEYARD"
    if part.startswith("ExileAnyGrave<"):
        return "ANY_GRAVEYARD"
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--out-tsv", type=Path, required=True)
    parser.add_argument("--out-plan", type=Path, required=True)
    args = parser.parse_args()

    forge = args.forge_root.resolve()
    rows = [
        json.loads(line)
        for line in args.ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    require(len(rows) == 4188, f"ledger cardinality {len(rows)} != 4188")

    targets = [
        row for row in rows
        if row.get("logical_bucket") == "WS33B"
        and row.get("implementation_target") == COST_TARGET
        and row.get("current_status") == "UNKNOWN"
    ]
    require(len(targets) == 402, f"target cardinality {len(targets)} != 402")

    cases = []
    skipped = Counter()
    for row in sorted(targets, key=lambda r: r["effective_path_id"]):
        provenances = row.get("source_provenance", [])
        chosen = None
        for prov in provenances:
            card_file = forge / prov["forge_source_path"]
            if not card_file.is_file():
                continue
            name, lines = read_card_text(card_file)
            if not name:
                continue
            if prov["source_directive"] == "ABILITY" and prov["source_token"] == "Cost$":
                try:
                    line_no = int(prov["source_line"])
                except ValueError:
                    continue
                if not has_activated_with_cost(lines, line_no):
                    continue
            chosen = (prov, name, lines)
            break
        if chosen is None:
            skipped["no_resolvable_provenance"] += 1
            continue
        prov, name, lines = chosen
        try:
            line_no = int(prov["source_line"]) if prov["source_directive"] != "MANA_COST" else 0
        except ValueError:
            skipped["bad_source_line"] += 1
            continue
        recipe, params = assign_recipe(name, prov["source_directive"], prov["source_token"],
                                       prov["source_value"], lines)
        cases.append({
            "path_id": row["effective_path_id"],
            "oracle_id": prov["oracle_identity"],
            "card_name": name,
            "directive": prov["source_directive"],
            "token": prov["source_token"],
            "cost_expression": prov["source_value"],
            "scenario_group": row["scenario_group_id"],
            "evidence_profile": row["evidence_profile"],
            "recipe": recipe,
            "recipe_params": params,
            "source_path": prov["forge_source_path"],
            "source_line": line_no,
        })

    require(cases, "no cost cases selected")
    args.out_tsv.parent.mkdir(parents=True, exist_ok=True)
    with args.out_tsv.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(
            "# path_id\toracle_id\tcard_name_b64\tdirective\ttoken_b64\tcost_expression_b64"
            "\tscenario_group\tevidence_profile\trecipe\trecipe_params_b64\tsource_path_b64\tsource_line\n"
        )
        for case in cases:
            handle.write("\t".join([
                case["path_id"],
                case["oracle_id"],
                b64(case["card_name"]),
                case["directive"],
                b64(case["token"]),
                b64(case["cost_expression"]),
                case["scenario_group"],
                case["evidence_profile"],
                case["recipe"],
                b64(json.dumps(case["recipe_params"], sort_keys=True)),
                b64(case["source_path"]),
                str(case["source_line"]),
            ]) + "\n")

    plan = {
        "schema": "commander-simulator-next.ws33-cost-campaign-plan.v1",
        "selection_policy": {
            "ledger": "WS33_INTEGRATED_CLOSURE_LEDGER.jsonl (4188 rows)",
            "logical_bucket": "WS33B",
            "implementation_target": COST_TARGET,
            "current_status": "UNKNOWN",
            "representative_policy": "first provenance resolvable against pinned Forge; Cost$ requires an A: ability line",
            "pilot_policy": "pay through production CostPayment/HumanCostDecision; choices only among authoritative options; fail closed",
        },
        "case_count": len(cases),
        "recipe_counts": dict(Counter(c["recipe"] for c in cases)),
        "skipped_counts": dict(skipped),
        "cases": cases,
    }
    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(
        {"WS33_COST_PREPARE": "PASS", "case_count": len(cases),
         "recipes": plan["recipe_counts"], "skipped": plan["skipped_counts"]},
        sort_keys=True))


if __name__ == "__main__":
    main()
