#!/usr/bin/env python3
"""Derive deterministic WS29 actual-card execution cases from the immutable WS26 V2 manifest.

The generator intentionally selects one exact pinned-Forge source occurrence per V2 path and
traces SVar references back to a real card root (A/T/S/K).  It never fabricates an ability
definition.  The Java qualification overlay consumes these cases against the card database
constructed by pinned Forge.
"""
import argparse
import json
import pathlib
import re


def directive_kind(line):
    if line.startswith("A:"):
        return "ABILITY"
    if line.startswith("T:"):
        return "TRIGGER"
    if line.startswith("S:"):
        return "STATIC"
    if line.startswith("K:"):
        return "KEYWORD"
    if line.startswith("SVar:"):
        return "SVAR"
    return "OTHER"


def svar_name(line):
    match = re.match(r"SVar:([^:]+):", line)
    return match.group(1) if match else None


def token_present(line, name):
    return re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", line) is not None


def roots_for(lines, source_line):
    source = lines[source_line - 1]
    if directive_kind(source) != "SVAR":
        return [(source_line, directive_kind(source), source)]

    definitions = {}
    for line_no, line in enumerate(lines, 1):
        name = svar_name(line)
        if name:
            definitions[name] = (line_no, line)

    queue = [svar_name(source)]
    seen = set()
    roots = []
    while queue:
        name = queue.pop(0)
        if not name or name in seen:
            continue
        seen.add(name)
        definition_line = definitions.get(name, (None, ""))[0]
        for line_no, line in enumerate(lines, 1):
            if line_no == definition_line or not token_present(line, name):
                continue
            kind = directive_kind(line)
            if kind == "SVAR":
                parent = svar_name(line)
                if parent and parent not in seen:
                    queue.append(parent)
            elif kind in {"ABILITY", "TRIGGER", "STATIC", "KEYWORD"}:
                roots.append((line_no, kind, line))

    roots = sorted(set(roots), key=lambda value: (value[0], value[1], value[2]))
    if not roots:
        raise RuntimeError(f"No card execution root for SVar at source line {source_line}: {source}")
    priority = {"ABILITY": 0, "TRIGGER": 1, "STATIC": 2, "KEYWORD": 3}
    return sorted(roots, key=lambda value: (priority.get(value[1], 9), value[0]))


def parse_api(line):
    match = re.search(r"(?:^A:)?(?:SP|AB)\$\s*([^|]+)", line)
    return match.group(1).strip() if match else ""


def parse_mode(line):
    match = re.search(r"Mode\$\s*([^|]+)", line)
    return match.group(1).strip() if match else ""


def parse_card_name(lines):
    for line in lines:
        if line.startswith("Name:"):
            return line.split(":", 1)[1].strip()
    raise RuntimeError("Pinned Forge card script has no Name directive")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--forge-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    manifest = json.loads(pathlib.Path(args.manifest).read_text(encoding="utf-8"))
    forge_root = pathlib.Path(args.forge_root)
    paths = [p for p in manifest["paths"] if p["owner_family"] == "CONTINUOUS_COPY_CONTROL"]
    if len(paths) != 301:
        raise SystemExit(f"Expected 301 CONTINUOUS_COPY_CONTROL paths, got {len(paths)}")

    rows = []
    for path in paths:
        source = sorted(
            path["source_provenance"],
            key=lambda item: (item["forge_source_path"], item["source_line"], item["oracle_identity"]),
        )[0]
        source_file = forge_root / source["forge_source_path"]
        lines = source_file.read_text(encoding="utf-8").splitlines()
        source_text = lines[source["source_line"] - 1]
        root_line, root_kind, root_text = roots_for(lines, source["source_line"])[0]
        if root_kind == "ABILITY":
            root_key = parse_api(root_text)
        elif root_kind in {"TRIGGER", "STATIC"}:
            root_key = parse_mode(root_text)
        elif root_kind == "KEYWORD" and root_text.startswith("K:"):
            root_key = root_text[2:].split(":", 1)[0].strip()
        else:
            root_key = ""

        rows.append(
            {
                "v2_path_id": path["v2_path_id"],
                "oracle_identity": source["oracle_identity"],
                "card_name": parse_card_name(lines),
                "source_path": source["forge_source_path"],
                "source_directive": source["source_directive"],
                "source_line": source["source_line"],
                "source_svar": svar_name(source_text) or "",
                "source_text": source_text,
                "dispatch_domain": path["dispatch_domain"],
                "dispatch_token": path["dispatch_token"],
                "implementation_target": path["implementation_target"],
                "root_kind": root_kind,
                "root_line": root_line,
                "root_key": root_key,
                "root_text": root_text,
                "selector_profile": path["semantic_selector_profile"],
                "parent_ws14_primitive_id": path["parent_ws14_primitive_id"],
                "required_decision_evidence": path["required_decision_evidence"],
                "required_hidden_info_evidence": path["required_hidden_info_evidence"],
                "required_replay_evidence": path["required_replay_evidence"],
                "required_rng_evidence": path["required_rng_evidence"],
                "representative_actual_oracle_identities": path["representative_actual_oracle_identities"],
                "source_occurrence_count": path["source_occurrence_count"],
                "cross_family_dependencies": path["cross_family_dependencies"],
            }
        )

    rows.sort(key=lambda row: row["v2_path_id"])
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "".join(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )

    summary = {
        "schema": "commander-simulator-next.ws29.case-summary.v1",
        "path_count": len(rows),
        "root_kind_counts": {},
        "dispatch_token_counts": {},
        "implementation_target_counts": {},
    }
    for row in rows:
        for field, key in (
            ("root_kind", "root_kind_counts"),
            ("dispatch_token", "dispatch_token_counts"),
            ("implementation_target", "implementation_target_counts"),
        ):
            summary[key][row[field]] = summary[key].get(row[field], 0) + 1
    pathlib.Path(str(out) + ".summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
