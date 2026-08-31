#!/usr/bin/env python3
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

SVAR_DOMAIN = "SVAR_RUNTIME_EXPRESSION"


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"


def record_fields(line: str) -> tuple[str, dict[str, str]] | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    # Forge card scripts use A:/S:/T:/R: records with pipe-separated Field$ Value terms.
    m = re.match(r"^([ASTR]):(.*)$", stripped)
    if not m:
        return None
    kind = m.group(1)
    body = m.group(2)
    fields: dict[str, str] = {}
    for part in body.split("|"):
        part = part.strip()
        if "$" not in part:
            continue
        key, value = part.split("$", 1)
        fields[key.strip()] = value.strip()
    return kind, fields


def svar_decl(line: str) -> tuple[str, str] | None:
    stripped = line.strip()
    if not stripped.startswith("SVar:"):
        return None
    rest = stripped[5:]
    if ":" not in rest:
        return None
    name, value = rest.split(":", 1)
    return name.strip(), value.strip()


def contains_token(value: str, token: str) -> bool:
    # SVar references are normally values of Foo$ TOKEN or embedded as TOKEN in comma/space lists.
    # Exact-token matching prevents accidental prefix matches such as DBFoo vs DBFoo2.
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(token) + r"(?![A-Za-z0-9_])", value) is not None


def index_card(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    svars: dict[str, dict] = {}
    semantic: list[dict] = []
    for line_no, line in enumerate(lines, 1):
        decl = svar_decl(line)
        if decl:
            name, value = decl
            svars[name] = {"line": line_no, "value": value, "text": line}
            continue
        parsed = record_fields(line)
        if parsed:
            kind, fields = parsed
            semantic.append({"line": line_no, "kind": kind, "fields": fields, "text": line})
    return lines, svars, semantic


def provenance_key(prov: dict) -> tuple[str, int]:
    return str(prov.get("forge_source_path", "")), int(prov.get("source_line", 0) or 0)


def terminal_path_index(paths: list[dict]):
    out: dict[tuple[str, int], list[dict]] = collections.defaultdict(list)
    for row in paths:
        if row.get("dispatch_domain") == SVAR_DOMAIN:
            continue
        for prov in row.get("source_provenance", []):
            key = provenance_key(prov)
            if key[0] and key[1] > 0:
                out[key].append(row)
    return out


def terminal_usages(start_token: str, svars: dict[str, dict], semantic: list[dict], terminal_idx: dict, relpath: str):
    # Reverse SVar dependency graph: child token -> SVar declarations that consume it.
    reverse: dict[str, list[str]] = collections.defaultdict(list)
    for outer, decl in svars.items():
        for inner in svars:
            if inner != outer and contains_token(decl["value"], inner):
                reverse[inner].append(outer)

    direct_semantic: dict[str, list[dict]] = collections.defaultdict(list)
    for rec in semantic:
        for field, value in rec["fields"].items():
            for token in svars:
                if contains_token(value, token):
                    direct_semantic[token].append({
                        "terminal_line": rec["line"],
                        "record_kind": rec["kind"],
                        "field": field,
                        "field_value": value,
                        "terminal_text": rec["text"],
                    })

    queue = collections.deque([(start_token, [start_token])])
    seen = set()
    usages: list[dict] = []
    while queue:
        token, chain = queue.popleft()
        if token in seen:
            continue
        seen.add(token)
        for rec in direct_semantic.get(token, []):
            terminal_paths = terminal_idx.get((relpath, rec["terminal_line"]), [])
            usages.append({
                **rec,
                "svar_chain": chain,
                "terminal_paths": [
                    {
                        "v2_path_id": p.get("v2_path_id"),
                        "implementation_target": p.get("implementation_target"),
                        "owner_family": p.get("owner_family"),
                        "dispatch_domain": p.get("dispatch_domain"),
                        "dispatch_token": p.get("dispatch_token"),
                        "evidence_profile": p.get("evidence_profile"),
                    }
                    for p in terminal_paths
                ],
            })
        for outer in reverse.get(token, []):
            if outer not in chain:
                queue.append((outer, chain + [outer]))
    return usages


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--forge-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    manifest = load(args.manifest)
    paths = manifest["paths"]
    terminal_idx = terminal_path_index(paths)
    srows = [p for p in paths if p.get("dispatch_domain") == SVAR_DOMAIN]
    cache: dict[str, tuple] = {}
    audit_rows = []
    field_counts = collections.Counter()
    field_parent_counts = collections.Counter()
    unresolved = []

    for row in srows:
        usages_all = []
        for prov in row.get("source_provenance", []):
            if prov.get("source_directive") != "SVAR":
                continue
            rel = str(prov.get("forge_source_path", ""))
            token = str(prov.get("source_token", ""))
            line_no = int(prov.get("source_line", 0) or 0)
            if not rel or not token:
                continue
            card = args.forge_root / rel
            if not card.is_file():
                unresolved.append({"v2_path_id": row["v2_path_id"], "reason": "CARD_SOURCE_MISSING", "source": rel})
                continue
            if rel not in cache:
                cache[rel] = index_card(card)
            _lines, svars, semantic = cache[rel]
            decl = svars.get(token)
            if not decl or decl["line"] != line_no:
                unresolved.append({
                    "v2_path_id": row["v2_path_id"], "reason": "SVAR_DECLARATION_MISMATCH",
                    "source": rel, "token": token, "expected_line": line_no,
                    "actual": decl,
                })
                continue
            usages = terminal_usages(token, svars, semantic, terminal_idx, rel)
            if not usages:
                unresolved.append({
                    "v2_path_id": row["v2_path_id"], "reason": "NO_SEMANTIC_CONSUMER",
                    "source": rel, "token": token, "line": line_no,
                })
            for usage in usages:
                field_counts[usage["field"]] += 1
                targets = tuple(sorted({p["implementation_target"] for p in usage["terminal_paths"] if p.get("implementation_target")}))
                owners = tuple(sorted({p["owner_family"] for p in usage["terminal_paths"] if p.get("owner_family")}))
                field_parent_counts[(usage["field"], targets, owners)] += 1
            usages_all.append({
                "oracle_identity": prov.get("oracle_identity"),
                "forge_source_path": rel,
                "source_line": line_no,
                "source_token": token,
                "source_value": prov.get("source_value"),
                "terminal_usages": usages,
            })
        audit_rows.append({
            "v2_path_id": row["v2_path_id"],
            "assigned_implementation_target": row.get("implementation_target"),
            "assigned_owner_family": row.get("owner_family"),
            "semantic_selector_profile": row.get("semantic_selector_profile"),
            "evidence_profile": row.get("evidence_profile"),
            "provenance": usages_all,
        })

    summary = {
        "schema": "commander-simulator-next.ws33-svar-consumer-audit.v1",
        "source_manifest": str(args.manifest),
        "svar_path_count": len(srows),
        "audited_path_count": len(audit_rows),
        "unresolved_count": len(unresolved),
        "field_counts": dict(sorted(field_counts.items())),
        "field_parent_counts": [
            {
                "field": field,
                "terminal_targets": list(targets),
                "terminal_owners": list(owners),
                "count": count,
            }
            for (field, targets, owners), count in sorted(field_parent_counts.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1], kv[0][2]))
        ],
        "unresolved": unresolved,
        "paths": audit_rows,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(canonical(summary), encoding="utf-8")

    print("SVAR_PATH_COUNT=" + str(len(srows)))
    print("UNRESOLVED_COUNT=" + str(len(unresolved)))
    print("FIELD_COUNTS=" + json.dumps(dict(sorted(field_counts.items())), sort_keys=True))
    print("TOP_FIELD_PARENT_COUNTS=")
    for rec in summary["field_parent_counts"][:80]:
        print(json.dumps(rec, sort_keys=True))
    if unresolved:
        print("UNRESOLVED_SAMPLE=")
        for rec in unresolved[:50]:
            print(json.dumps(rec, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
