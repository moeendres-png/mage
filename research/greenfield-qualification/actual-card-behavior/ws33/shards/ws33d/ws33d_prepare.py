#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import collections
import hashlib
import json
import re
from pathlib import Path

BASE_HEAD = "c69686431c7296cb3e1a2f9e0de8b82886c92c46"
BASE_TREE = "6b885d02e9a0bc8cad2f93af08db99bda75955a5"
FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"

EXCLUDED_SIBLING_TARGETS = {
    "forge.game.cost.Cost",
    "forge.game.spellability.AbilitySub",
    "forge.game.ability.AbilityUtils#calculateAmount",
    "forge.game.spellability.TargetRestrictions",
    "forge.game.spellability.SpellApiBased",
    "forge.game.spellability.AbilityApiBased",
}

EXPECTED_EVIDENCE = {
    "STATE_ONLY": 292,
    "DECISION+RNG+REPLAY": 271,
    "DECISION+REPLAY": 225,
    "DECISION+HIDDEN+REPLAY": 134,
    "DECISION+RNG+HIDDEN+REPLAY": 38,
    "HIDDEN": 3,
}

STATE_BY_MODE = {
    "Split": ("LeftSplit", "RightSplit"),
    "Prepare": ("Original", "PreparedSpell"),
    "Adventure": ("Original", "Secondary"),
    "Omen": ("Original", "Secondary"),
    "Modal": ("Original", "Backside"),
    "Transform": ("Original", "Backside"),
    "DoubleFaced": ("Original", "Backside"),
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit("WS33D_PREPARE=FAIL " + message)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def evidence_profile(path: dict) -> str:
    names = []
    for name, key in (
        ("DECISION", "required_decision_evidence"),
        ("RNG", "required_rng_evidence"),
        ("HIDDEN", "required_hidden_info_evidence"),
        ("REPLAY", "required_replay_evidence"),
    ):
        if path.get(key):
            names.append(name)
    return "+".join(names) if names else "STATE_ONLY"


def parse_script(lines: list[str]) -> dict:
    name = next((line[5:].strip() for line in lines if line.startswith("Name:")), "")
    alt_mode = next((line.split(":", 1)[1].strip() for line in lines if line.startswith("AlternateMode:")), "None")
    alt_line = next((i + 1 for i, line in enumerate(lines) if line.strip() == "ALTERNATE"), None)
    a_records: list[tuple[int, str]] = []
    t_records: list[tuple[int, str]] = []
    s_records: list[tuple[int, str]] = []
    k_records: list[tuple[int, str]] = []
    svars: dict[str, tuple[int, str]] = {}
    for i, raw in enumerate(lines, 1):
        line = raw.strip()
        if line.startswith("A:"):
            a_records.append((i, line[2:].strip()))
        elif line.startswith("T:"):
            t_records.append((i, line[2:].strip()))
        elif line.startswith("S:"):
            s_records.append((i, line[2:].strip()))
        elif line.startswith("K:"):
            k_records.append((i, line[2:].strip()))
        elif line.startswith("SVar:"):
            parts = line.split(":", 2)
            if len(parts) == 3:
                svars[parts[1].strip()] = (i, parts[2].strip())
    return {
        "name": name,
        "alt_mode": alt_mode,
        "alt_line": alt_line,
        "A": a_records,
        "T": t_records,
        "S": s_records,
        "K": k_records,
        "SVAR": svars,
    }


def source_state(script: dict, line_no: int) -> str:
    primary, alternate = STATE_BY_MODE.get(script["alt_mode"], ("Original", "Original"))
    return alternate if script["alt_line"] is not None and line_no > script["alt_line"] else primary


def ability_map(body: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for field in body.split("|"):
        field = field.strip()
        if "$" not in field:
            continue
        key, value = field.split("$", 1)
        result[key.strip()] = value.strip()
    return result


def map_signature(body: str) -> str:
    params = ability_map(body)
    canonical = "\x1f".join(f"{k}={params[k]}" for k in sorted(params))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def api_from_body(body: str) -> tuple[str, str]:
    fields = body.split("|", 1)[0].strip()
    if "$" not in fields:
        return "", ""
    prefix, api = [part.strip() for part in fields.split("$", 1)]
    return prefix, api


def tokens(body: str) -> set[str]:
    return set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", body))


def find_root_for_svar(script: dict, target: str) -> tuple[str, int, str, list[str]] | None:
    """Find a deterministic actual top-level A record that reaches target through SVar refs."""
    svars: dict[str, tuple[int, str]] = script["SVAR"]
    if target not in svars:
        return None
    names = set(svars)
    reverse: dict[str, list[tuple[str, str, int, str]]] = collections.defaultdict(list)
    for parent, (line_no, body) in svars.items():
        for child in sorted(tokens(body) & names):
            if child != parent:
                reverse[child].append(("SVAR", parent, line_no, body))
    for kind in ("A", "T", "K", "S"):
        for line_no, body in script[kind]:
            for child in sorted(tokens(body) & names):
                reverse[child].append((kind, "", line_no, body))

    queue: collections.deque[tuple[str, list[str]]] = collections.deque([(target, [target])])
    seen = {target}
    non_a_candidates = []
    while queue:
        node, chain = queue.popleft()
        parents = sorted(reverse.get(node, []), key=lambda x: (0 if x[0] == "A" else 1, x[2], x[1], x[3]))
        for kind, parent_name, line_no, body in parents:
            if kind == "A":
                return ("A", line_no, body, chain)
            if kind in {"T", "K", "S"}:
                non_a_candidates.append((kind, line_no, body, chain))
                continue
            if parent_name not in seen:
                seen.add(parent_name)
                queue.append((parent_name, [parent_name] + chain))
    if non_a_candidates:
        non_a_candidates.sort(key=lambda x: ({"T": 0, "K": 1, "S": 2}[x[0]], x[1], x[2]))
        return non_a_candidates[0]
    line_no, body = svars[target]
    prefix, _ = api_from_body(body)
    if prefix in {"AB", "SP"}:
        return ("SVAR_ROOT", line_no, body, [target])
    return None


def candidate_for_provenance(path: dict, prov: dict, forge: Path) -> dict | None:
    rel = prov.get("forge_source_path", "")
    source_path = forge / rel
    if not source_path.is_file():
        return None
    lines = source_path.read_text(encoding="utf-8", errors="replace").splitlines()
    line_no = int(prov["source_line"])
    if not (1 <= line_no <= len(lines)):
        return None
    script = parse_script(lines)
    if not script["name"]:
        return None
    raw = lines[line_no - 1].strip()
    directive = prov.get("source_directive")
    target_body = ""
    target_svar = ""
    if directive == "ABILITY" and raw.startswith("A:"):
        target_body = raw[2:].strip()
        root = ("A", line_no, target_body, [])
    elif directive == "SVAR" and raw.startswith("SVar:"):
        parts = raw.split(":", 2)
        if len(parts) != 3:
            return None
        target_svar = parts[1].strip()
        target_body = parts[2].strip()
        root = find_root_for_svar(script, target_svar)
    else:
        root = None
        target_body = raw

    target_prefix, target_api = api_from_body(target_body)
    if path["dispatch_domain"] == "ABILITY_API":
        if not target_api or target_api != path["dispatch_token"]:
            return None
    root_kind = root[0] if root else "SPECIALIZED"
    root_line = root[1] if root else 0
    root_body = root[2] if root else ""
    chain = root[3] if root else []
    return {
        "oracle_id": prov["oracle_identity"],
        "card_name": script["name"],
        "source_path": rel,
        "source_line": line_no,
        "source_directive": directive,
        "target_svar": target_svar,
        "target_body": target_body,
        "target_prefix": target_prefix,
        "target_api": target_api,
        "target_signature": map_signature(target_body) if target_api else "",
        "ability_state": source_state(script, root_line or line_no),
        "root_kind": root_kind,
        "root_line": root_line,
        "root_body": root_body,
        "root_prefix": api_from_body(root_body)[0] if root_body else "",
        "root_api": api_from_body(root_body)[1] if root_body else "",
        "svar_chain": chain,
    }


def choose_case(path: dict, forge: Path) -> dict:
    candidates = []
    for prov in sorted(
        path.get("source_provenance", []),
        key=lambda item: (item.get("oracle_identity", ""), item.get("forge_source_path", ""), int(item.get("source_line", 0))),
    ):
        candidate = candidate_for_provenance(path, prov, forge)
        if candidate:
            candidates.append(candidate)
    require(candidates, f"no actual pinned-Forge source occurrence for {path['v2_path_id']}")
    rank = {"A": 0, "SVAR_ROOT": 1, "T": 2, "K": 3, "S": 4, "SPECIALIZED": 5}
    candidates.sort(key=lambda c: (rank.get(c["root_kind"], 9), c["source_path"], c["source_line"], c["oracle_id"]))
    chosen = candidates[0]
    chosen.update({
        "path_id": path["v2_path_id"],
        "parent_primitive_id": path["parent_ws14_primitive_id"],
        "implementation_target": path["implementation_target"],
        "dispatch_domain": path["dispatch_domain"],
        "dispatch_token": path["dispatch_token"],
        "evidence_profile": evidence_profile(path),
        "required_decision": bool(path["required_decision_evidence"]),
        "required_rng": bool(path["required_rng_evidence"]),
        "required_hidden": bool(path["required_hidden_info_evidence"]),
        "required_replay": bool(path["required_replay_evidence"]),
        "semantic_selector_profile": path["semantic_selector_profile"],
        "source_occurrence_count": path["source_occurrence_count"],
    })
    return chosen


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--coverage", type=Path, required=True)
    parser.add_argument("--forge-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = load(args.manifest)
    coverage = load(args.coverage)
    forge = args.forge_root.resolve()

    require(manifest["source_head"] == BASE_HEAD, f"manifest source_head={manifest['source_head']}")
    require(manifest["source_tree"] == BASE_TREE, f"manifest source_tree={manifest['source_tree']}")
    require(manifest["forge_pin"] == FORGE_PIN, f"manifest forge_pin={manifest['forge_pin']}")
    coverage_by_id = {row["effective_v2_path_id"]: row for row in coverage["paths"]}

    scope = [
        path for path in manifest["paths"]
        if path["owner_family"] == "ACTION_COST_DECISION"
        and coverage_by_id[path["v2_path_id"]]["status"] == "UNKNOWN"
        and path["implementation_target"] not in EXCLUDED_SIBLING_TARGETS
    ]
    require(len(scope) == 963, f"assigned scope expected 963, found {len(scope)}")
    require(len({p["v2_path_id"] for p in scope}) == 963, "duplicate path ids in assigned scope")

    evidence_counts = collections.Counter(evidence_profile(path) for path in scope)
    require(dict(evidence_counts) == EXPECTED_EVIDENCE,
            f"evidence profile mismatch actual={dict(evidence_counts)} expected={EXPECTED_EVIDENCE}")

    target_counts = collections.Counter(path["implementation_target"] for path in scope)
    cases = [choose_case(path, forge) for path in scope]
    cases.sort(key=lambda c: (-target_counts[c["implementation_target"]], c["implementation_target"], c["path_id"]))

    root_counts = collections.Counter(c["root_kind"] for c in cases)
    dispatch_counts = collections.Counter(c["dispatch_domain"] for c in cases)
    api_rootable = sum(1 for c in cases if c["dispatch_domain"] == "ABILITY_API" and c["root_kind"] in {"A", "SVAR_ROOT"})

    args.out.mkdir(parents=True, exist_ok=True)
    plan = {
        "schema": "commander-simulator-next.ws33d-campaign-plan.v1",
        "source_head": BASE_HEAD,
        "source_tree": BASE_TREE,
        "forge_pin": FORGE_PIN,
        "scope_predicate": {
            "coverage_status": "UNKNOWN",
            "owner_family": "ACTION_COST_DECISION",
            "excluded_sibling_implementation_targets": sorted(EXCLUDED_SIBLING_TARGETS),
        },
        "assigned_paths_total": len(cases),
        "implementation_target_counts": dict(target_counts.most_common()),
        "evidence_profile_counts": dict(evidence_counts),
        "dispatch_domain_counts": dict(dispatch_counts),
        "root_kind_counts": dict(root_counts),
        "ability_api_directly_rootable_count": api_rootable,
        "cases": cases,
    }
    (args.out / "WS33D_CAMPAIGN_PLAN.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    with (args.out / "ws33d-cases.tsv").open("w", encoding="utf-8", newline="\n") as handle:
        handle.write("# " + "\t".join([
            "path_id", "parent_primitive_id", "implementation_target", "dispatch_domain", "dispatch_token",
            "evidence_profile", "oracle_id", "card_name_b64", "source_path_b64", "source_line",
            "source_directive", "ability_state", "root_kind", "root_line", "root_body_b64",
            "target_svar_b64", "target_api", "target_signature", "selector_json_b64",
        ]) + "\n")
        for c in cases:
            handle.write("\t".join([
                c["path_id"], c["parent_primitive_id"], c["implementation_target"], c["dispatch_domain"],
                c["dispatch_token"], c["evidence_profile"], c["oracle_id"], b64(c["card_name"]),
                b64(c["source_path"]), str(c["source_line"]), c["source_directive"], c["ability_state"],
                c["root_kind"], str(c["root_line"]), b64(c["root_body"]), b64(c["target_svar"]),
                c["target_api"], c["target_signature"],
                b64(json.dumps(c["semantic_selector_profile"], sort_keys=True, separators=(",", ":"))),
            ]) + "\n")

    print(json.dumps({
        "WS33D_PREPARE": "PASS",
        "assigned_paths_total": 963,
        "root_kind_counts": dict(root_counts),
        "ability_api_directly_rootable_count": api_rootable,
        "top_targets": target_counts.most_common(20),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
