#!/usr/bin/env python3
"""Materialize the exact post-A1 WS33A TargetRestrictions remainder.

This is provenance/topology preparation only. It never interprets ValidTgts as
legality and never mutates coverage. Actual target legality remains Forge-owned
at runtime.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
CONSUMER_MODEL_SHA256 = "82638e6b3e4408cc5bddedc49372b6357d3c2bdce6fba7bfab7ed119678f9a48"
EXPECTED_MANIFEST_SHA256 = "cd48f4279d682ab944e2534bf937d87e5311e83989e97179ae73c5c7d1bb6224"
EXPECTED_PROFILES = {
    "ws33-g2-template-122": ("DECISION+HIDDEN+REPLAY", 53),
    "ws33-g2-template-124": ("DECISION+RNG+HIDDEN+REPLAY", 2),
    "ws33-g2-template-125": ("DECISION+RNG+REPLAY", 2),
}
FIELD_RE = re.compile(r"(?:^|\s\|\s)([A-Za-z][A-Za-z0-9_]*)\$\s*([^|]*?)(?=\s*\|\s|$)")
TOKEN_SPLIT_RE = re.compile(r"[\s,;]+")
ABILITY_RE = re.compile(r"^(AB|SP|DB)\$\s*([^|]+)")


def fail(message: str) -> None:
    raise SystemExit("WS33_A_REST_TOPOLOGY=FAIL " + message)


def require(condition: bool, message: str) -> None:
    if not condition:
        fail(message)


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    import hashlib
    return hashlib.sha256(path.read_bytes()).hexdigest()


def b64(value: str) -> str:
    return base64.b64encode(value.encode("utf-8")).decode("ascii")


def card_name(lines: list[str], source: Path) -> str:
    for line in lines:
        if line.startswith("Name:"):
            return line.split(":", 1)[1].strip()
    fail("card source missing Name: " + source.as_posix())


def source_script_and_svar(line: str, directive: str) -> tuple[str, str | None]:
    line = line.strip()
    if directive == "ABILITY":
        require(":" in line, "malformed ABILITY source line")
        return line.split(":", 1)[1].strip(), None
    if directive == "SVAR":
        parts = line.split(":", 2)
        require(len(parts) == 3 and parts[0] == "SVar", "malformed SVAR source line")
        return parts[2].strip(), parts[1].strip()
    fail("unsupported source directive " + directive)


def field_map(script: str) -> dict[str, str]:
    return {m.group(1): m.group(2).strip() for m in FIELD_RE.finditer(script)}


def ability_identity(script: str) -> tuple[str, str]:
    first = script.split("|", 1)[0].strip()
    m = ABILITY_RE.match(first)
    require(m is not None, "source script is not an AB/SP/DB ability: " + first)
    return m.group(1), m.group(2).strip()


def referenced_fields(script: str, target_name: str) -> list[str]:
    out: list[str] = []
    for m in FIELD_RE.finditer(script):
        tokens = {x for x in TOKEN_SPLIT_RE.split(m.group(2).strip()) if x}
        if target_name in tokens:
            out.append(m.group(1))
    return out


def parent_candidates(lines: list[str], target_name: str, target_line: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for index, line in enumerate(lines, 1):
        if index == target_line:
            continue
        stripped = line.strip()
        if stripped.startswith("SVar:"):
            parts = stripped.split(":", 2)
            if len(parts) != 3:
                continue
            directive = "SVAR"
            parent_svar = parts[1].strip()
            script = parts[2].strip()
        elif ":" in stripped and stripped[0] in "ATRS":
            directive = {"A": "ABILITY", "T": "TRIGGER", "R": "REPLACEMENT", "S": "STATIC"}[stripped[0]]
            parent_svar = None
            script = stripped.split(":", 1)[1].strip()
        else:
            continue
        for consumer_field in referenced_fields(script, target_name):
            first = script.split("|", 1)[0].strip()
            af = bool(ABILITY_RE.match(first))
            fields = field_map(script)
            out.append({
                "source_line": index,
                "directive": directive,
                "parent_svar": parent_svar,
                "consumer_field": consumer_field,
                "script": script,
                "ability_factory_compatible": af,
                "event_mode": fields.get("Mode", "") if directive == "TRIGGER" else "",
            })
    return out


def consumer_signature(parent: dict[str, Any]) -> tuple[str, str, bool]:
    return parent["directive"], parent["consumer_field"], bool(parent["ability_factory_compatible"])


def select_parent_set(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    compatible = [x for x in candidates if x["ability_factory_compatible"]]
    pool = compatible if compatible else candidates
    signatures = {consumer_signature(x) for x in pool}
    if len(signatures) != 1:
        return []
    return sorted(pool, key=lambda x: (x["source_line"], x["directive"], x["consumer_field"], x["script"]))


def evidence_profile(path: dict[str, Any]) -> str:
    names: list[str] = []
    for name, key in (
        ("DECISION", "required_decision_evidence"),
        ("RNG", "required_rng_evidence"),
        ("HIDDEN", "required_hidden_info_evidence"),
        ("REPLAY", "required_replay_evidence"),
    ):
        if path.get(key):
            names.append(name)
    return "+".join(names) if names else "STATE_ONLY"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model-dir", type=Path, required=True)
    ap.add_argument("--queue", type=Path, required=True)
    ap.add_argument("--forge-root", type=Path, required=True)
    ap.add_argument("--out-json", type=Path, required=True)
    ap.add_argument("--direct-tsv", type=Path, required=True)
    ap.add_argument("--svar-tsv", type=Path, required=True)
    args = ap.parse_args()

    model = args.model_dir.resolve()
    forge = args.forge_root.resolve()
    manifest_path = model / "WS33_EFFECTIVE_BEHAVIOR_PATH_MANIFEST.json"
    coverage_path = model / "WS33_PATH_COVERAGE.json"
    require(manifest_path.is_file() and coverage_path.is_file(), "incomplete model directory")
    require(sha256(manifest_path) == EXPECTED_MANIFEST_SHA256, "effective manifest digest mismatch")
    head = subprocess.check_output(["git", "-C", str(forge), "rev-parse", "HEAD"], text=True).strip()
    require(head == FORGE_PIN, "Forge pin mismatch " + head)

    manifest = load(manifest_path)
    coverage = load(coverage_path)
    queue = load(args.queue)
    require(manifest.get("path_count") == 4188 and len(manifest.get("paths", [])) == 4188, "manifest cardinality mismatch")
    require(manifest.get("consumer_model_sha256") == CONSUMER_MODEL_SHA256, "consumer model lineage mismatch")

    coverage_by = {x["effective_v2_path_id"]: x for x in coverage["paths"]}
    status_counts = Counter(x["status"] for x in coverage["paths"])
    require(status_counts == Counter({"PASS": 488, "UNKNOWN": 3700}), "predecessor coverage is not 488/3700 fail-closed frontier")

    selected_items = []
    for item in queue.get("items", []):
        if item.get("logical_bucket") != "WS33A":
            continue
        if item.get("runtime_subsystem") != "forge.game.spellability.TargetRestrictions":
            continue
        if item.get("scenario_group_id") not in EXPECTED_PROFILES:
            continue
        selected_items.append(item)
    require(len(selected_items) == 3, "expected exactly three A-rest queue items")
    ids: set[str] = set()
    profile_by_id: dict[str, tuple[str, str]] = {}
    for item in selected_items:
        expected_profile, expected_count = EXPECTED_PROFILES[item["scenario_group_id"]]
        require(item.get("evidence_profile") == expected_profile, "queue evidence profile mismatch " + item["scenario_group_id"])
        path_ids = item.get("effective_path_ids", [])
        require(item.get("unresolved_path_count") == expected_count and len(path_ids) == expected_count and len(set(path_ids)) == expected_count,
                "queue cardinality mismatch " + item["scenario_group_id"])
        for path_id in path_ids:
            require(path_id not in ids, "A-rest queue items overlap " + path_id)
            ids.add(path_id)
            profile_by_id[path_id] = (item["scenario_group_id"], expected_profile)
    require(len(ids) == 57, "A-rest union cardinality mismatch")
    require(all(path_id in coverage_by and coverage_by[path_id]["status"] == "UNKNOWN" for path_id in ids), "A-rest contains non-UNKNOWN predecessor path")

    path_by = {x["v2_path_id"]: x for x in manifest["paths"]}
    direct_rows: list[dict[str, Any]] = []
    svar_rows: list[dict[str, Any]] = []
    unresolved_svar: list[str] = []
    parent_shape_counts: Counter[str] = Counter()

    for ordinal, path_id in enumerate(sorted(ids), 1):
        path = path_by[path_id]
        require(path["owner_family"] == "ACTION_COST_DECISION", path_id + " owner mismatch")
        require(path["implementation_target"] == "forge.game.spellability.TargetRestrictions", path_id + " runtime target mismatch")
        require(evidence_profile(path) == profile_by_id[path_id][1], path_id + " manifest evidence profile mismatch")
        provenance = path.get("source_provenance", [])
        require(bool(provenance), path_id + " missing provenance")
        chosen = provenance[0]
        require(chosen.get("source_token") == "ValidTgts$", path_id + " source token is not ValidTgts$")
        directive = chosen.get("source_directive")
        require(directive in {"ABILITY", "SVAR"}, path_id + " unsupported source directive " + str(directive))
        source = forge / chosen["forge_source_path"]
        require(source.is_file(), path_id + " Forge source missing " + chosen["forge_source_path"])
        lines = source.read_text(encoding="utf-8").splitlines()
        line_no = int(chosen["source_line"])
        require(1 <= line_no <= len(lines), path_id + " source line out of range")
        script, svar_name = source_script_and_svar(lines[line_no - 1], directive)
        fields = field_map(script)
        require(fields.get("ValidTgts") == chosen.get("source_value"), path_id + " source ValidTgts mismatch")
        common = {
            "ordinal": ordinal,
            "v2_path_id": path_id,
            "scenario_group_id": profile_by_id[path_id][0],
            "evidence_profile": profile_by_id[path_id][1],
            "oracle_identity": chosen["oracle_identity"],
            "card_name": card_name(lines, source),
            "source_path": chosen["forge_source_path"],
            "source_line": line_no,
            "source_directive": directive,
            "valid_tgts": chosen["source_value"],
            "origin": fields.get("Origin", fields.get("TgtZone", "")),
            "destination": fields.get("Destination", ""),
            "cost_shape": path.get("semantic_selector_profile", {}).get("cost_shape", ""),
            "required_decision_evidence": bool(path.get("required_decision_evidence")),
            "required_rng_evidence": bool(path.get("required_rng_evidence")),
            "required_hidden_info_evidence": bool(path.get("required_hidden_info_evidence")),
            "required_replay_evidence": bool(path.get("required_replay_evidence")),
            "exact_script": script,
        }
        if directive == "ABILITY":
            ability_kind, api = ability_identity(script)
            common.update({"ability_kind": ability_kind, "api": api})
            direct_rows.append(common)
        else:
            require(bool(svar_name), path_id + " target SVar name missing")
            candidates = parent_candidates(lines, svar_name, line_no)
            selected = select_parent_set(candidates) if candidates else []
            if not selected:
                unresolved_svar.append(path_id)
            for parent in selected:
                parent_shape_counts[f"{parent['directive']}:{parent['consumer_field']}:{'AF' if parent['ability_factory_compatible'] else 'NON_AF'}"] += 1
            common.update({
                "target_svar": svar_name,
                "parent_candidates": candidates,
                "selected_parents": selected,
                "parent_entrypoint_count": len(selected),
                "requires_all_selected_parent_entrypoints": len(selected) > 1,
            })
            svar_rows.append(common)

    require(len(direct_rows) == 31, "direct ABILITY cardinality mismatch")
    require(len(svar_rows) == 26, "SVAR cardinality mismatch")
    require(not unresolved_svar, "unresolved/ambiguous SVar parents: " + ",".join(unresolved_svar))
    parent_entrypoints = sum(x["parent_entrypoint_count"] for x in svar_rows)
    require(parent_entrypoints >= 26, "SVar parent entrypoint coverage is incomplete")

    out = {
        "schema": "commander-simulator-next.ws33-a-rest-topology.v1",
        "status": "PASS",
        "forge_pin": FORGE_PIN,
        "effective_manifest_sha256": EXPECTED_MANIFEST_SHA256,
        "consumer_model_sha256": CONSUMER_MODEL_SHA256,
        "predecessor_path_status_counts": {k: status_counts.get(k, 0) for k in ("PASS", "UNKNOWN", "FAIL", "UNSUPPORTED")},
        "a_rest_path_count": len(ids),
        "direct_ability_path_count": len(direct_rows),
        "svar_path_count": len(svar_rows),
        "svar_parent_entrypoint_count": parent_entrypoints,
        "queue_units": [
            {"scenario_group_id": item["scenario_group_id"], "evidence_profile": item["evidence_profile"], "path_count": item["unresolved_path_count"]}
            for item in sorted(selected_items, key=lambda x: x["scenario_group_id"])
        ],
        "parent_shape_counts": dict(sorted(parent_shape_counts.items())),
        "unresolved_svar_paths": unresolved_svar,
        "coverage_mutated": False,
        "direct_cases": direct_rows,
        "svar_cases": svar_rows,
    }
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    with args.direct_tsv.open("w", encoding="utf-8", newline="\n") as handle:
        for row in direct_rows:
            values = [
                str(row["ordinal"]), row["v2_path_id"], row["oracle_identity"], row["card_name"],
                row["scenario_group_id"], row["evidence_profile"], row["ability_kind"], row["api"],
                row["source_path"], str(row["source_line"]), b64(row["exact_script"]), b64(row["valid_tgts"]),
                b64(row["origin"]), b64(row["destination"]), row["cost_shape"],
                "1" if row["required_decision_evidence"] else "0",
                "1" if row["required_rng_evidence"] else "0",
                "1" if row["required_hidden_info_evidence"] else "0",
                "1" if row["required_replay_evidence"] else "0",
            ]
            handle.write("\t".join(values) + "\n")

    with args.svar_tsv.open("w", encoding="utf-8", newline="\n") as handle:
        for row in svar_rows:
            for entry_index, parent in enumerate(row["selected_parents"], 1):
                values = [
                    str(row["ordinal"]), row["v2_path_id"], str(entry_index), str(row["parent_entrypoint_count"]),
                    row["oracle_identity"], row["card_name"], row["scenario_group_id"], row["evidence_profile"],
                    row["target_svar"], row["source_path"], str(row["source_line"]), b64(row["exact_script"]),
                    b64(row["valid_tgts"]), b64(row["origin"]), b64(row["destination"]), row["cost_shape"],
                    parent["directive"], parent.get("parent_svar") or "", parent["consumer_field"],
                    parent.get("event_mode", ""), str(parent["source_line"]), b64(parent["script"]),
                    "1" if row["required_decision_evidence"] else "0",
                    "1" if row["required_rng_evidence"] else "0",
                    "1" if row["required_hidden_info_evidence"] else "0",
                    "1" if row["required_replay_evidence"] else "0",
                ]
                handle.write("\t".join(values) + "\n")

    print(json.dumps({
        "WS33_A_REST_TOPOLOGY": "PASS",
        "paths": len(ids),
        "direct": len(direct_rows),
        "svar": len(svar_rows),
        "svar_parent_entrypoints": parent_entrypoints,
        "coverage_mutated": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
