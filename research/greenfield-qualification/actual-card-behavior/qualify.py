#!/usr/bin/env python3
"""WS10 actual-card behavioral qualification.

This harness is deliberately fail-closed. Exact Oracle identity membership comes
from the read-only WS02 corpus. Forge source presence and CardDb loadability are
useful evidence, but neither is promoted to semantic execution or behavior
verification.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import uuid
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
BASE_SHA = "c0e42fb42c4a603aff4a76b1284f8271c12bfd42"
SCHEMA = "commander-simulator-next.actual-card-behavior.v1"
CLASSIFICATIONS = {"FULL", "CONDITIONAL_FULL", "PARTIAL", "UNKNOWN", "UNSUPPORTED"}
DECISION_RE = re.compile(r"(?i)(Choose|Choice|Choices\$|Target|Targets|Optional|Mode\$|Vote|UnlessCost|Confirm|SelectPlayer|SelectCard)")
HIDDEN_RE = re.compile(r"(?i)(Library|Hand|Draw|Search|Reveal|Look(?: at)?|FaceDown|ExileFaceDown|Manifest|Cloak|Foretell|Plot)")
RNG_RE = re.compile(r"(?i)(Random|Shuffle|Coin|FlipCoin|RollDice|Dice|RandomNum)")
BEHAVIOR_RE = re.compile(r"(?m)^(?:A|T|S|R|K):")
SUSPICIOUS = {
    "TODO": re.compile(r"(?i)\btodo\b"),
    "UNSUPPORTED": re.compile(r"(?i)\bunsupported\b"),
    "NOT_IMPLEMENTED": re.compile(r"(?i)not implemented"),
    "DUMMY": re.compile(r"(?i)\bdummy\b"),
    "PLACEHOLDER": re.compile(r"(?i)\bplaceholder\b"),
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def decode_union(ws02: Path, union: dict[str, Any]) -> list[tuple[str, int]]:
    if union.get("schema") != "commander-simulator-next.actual-card-requirement-union.v2":
        raise ValueError("unexpected WS02 union schema")
    if union.get("status") != "PASS" or union.get("complete") is not True:
        raise ValueError("WS02 union is not PASS/complete")
    chunks = union.get("member_chunks") or union.get("membership_chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("WS02 union has no member chunks")
    out: list[tuple[str, int]] = []
    seen: set[str] = set()
    prev = ""
    for chunk in chunks:
        rel = chunk.get("path")
        if not isinstance(rel, str):
            raise ValueError("invalid union chunk path")
        path = ws02 / "research/greenfield-qualification" / rel
        if not path.exists():
            raise ValueError(f"missing union chunk: {rel}")
        if sha256(path) != chunk.get("sha256"):
            raise ValueError(f"union chunk hash mismatch: {rel}")
        if chunk.get("encoding") != "uuid16-mask8-base64-v1":
            raise ValueError(f"unsupported union chunk encoding: {rel}")
        raw = base64.b64decode(path.read_text(encoding="utf-8").strip(), validate=True)
        if len(raw) % 17:
            raise ValueError(f"invalid union chunk byte length: {rel}")
        rows = [raw[i:i + 17] for i in range(0, len(raw), 17)]
        if chunk.get("count") != len(rows):
            raise ValueError(f"union chunk count mismatch: {rel}")
        for raw_row in rows:
            oid = str(uuid.UUID(bytes=raw_row[:16]))
            mask = raw_row[16]
            if not mask or mask & ~31:
                raise ValueError(f"invalid source mask for {oid}: {mask}")
            if oid in seen or oid <= prev:
                raise ValueError("union Oracle IDs are not globally sorted unique")
            seen.add(oid)
            prev = oid
            out.append((oid, mask))
    expected = union.get("computed_oracle_id_count")
    if expected != len(out) or union.get("target_count") != len(out):
        raise ValueError(f"union count mismatch: decoded={len(out)} expected={expected}")
    return out


def forge_scripts(cards_root: Path) -> dict[str, list[dict[str, Any]]]:
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for path in sorted(cards_root.rglob("*.txt")):
        try:
            text = path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            text = path.read_text(encoding="latin1")
        name = None
        for line in text.splitlines():
            if line.startswith("Name:"):
                name = line[5:].strip()
                break
        if not name:
            continue
        by_name[name].append({
            "path": str(path.relative_to(cards_root.parent.parent.parent)),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "decision_path": bool(DECISION_RE.search(text)),
            "hidden_info_path": bool(HIDDEN_RE.search(text)),
            "rng_path": bool(RNG_RE.search(text)),
            "behavior_scripted": bool(BEHAVIOR_RE.search(text)),
            "suspicious_markers": sorted(k for k, rx in SUSPICIOUS.items() if rx.search(text)),
        })
    return by_name


def prepare(args: argparse.Namespace) -> int:
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    union_path = args.ws02 / "research/greenfield-qualification/ACTUAL_CARD_REQUIREMENT_UNION.json"
    pin_path = args.ws02 / "research/greenfield-qualification/ACTUAL_CARD_REQUIREMENT_ORACLE_PIN.json"
    union = read_json(union_path)
    pin = read_json(pin_path)
    members = decode_union(args.ws02, union)
    index = read_json(args.oracle_index)
    if pin.get("status") != "PASS":
        raise ValueError("WS02 Oracle pin is not PASS")
    if pin.get("index_sha256") != sha256(args.oracle_index):
        raise ValueError("reconstructed Scryfall index hash differs from WS02 pin")
    if index.get("oracle_identity_count") != pin.get("oracle_identity_count"):
        raise ValueError("Scryfall index identity count differs from WS02 pin")
    by_id = {r.get("oracle_id"): r for r in index.get("cards", []) if isinstance(r, dict)}
    scripts = forge_scripts(args.forge_cards)
    rows: list[dict[str, Any]] = []
    names: list[str] = []
    mapping_gaps: list[dict[str, Any]] = []
    for oid, mask in members:
        oracle = by_id.get(oid)
        if not oracle:
            raise ValueError(f"requirement Oracle ID absent from reconstructed index: {oid}")
        name = oracle.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError(f"missing canonical Oracle name: {oid}")
        exact = scripts.get(name, [])
        face_candidates: list[dict[str, Any]] = []
        if not exact:
            for face in oracle.get("face_names") or []:
                if isinstance(face, str) and face in scripts:
                    face_candidates.extend({"face_name": face, **x} for x in scripts[face])
        candidates = exact if exact else face_candidates
        decision = any(x["decision_path"] for x in candidates)
        hidden = any(x["hidden_info_path"] for x in candidates)
        rng = any(x["rng_path"] for x in candidates)
        behavior = any(x["behavior_scripted"] for x in candidates)
        suspicious = sorted({m for x in candidates for m in x["suspicious_markers"]})
        source_present = "PASS" if exact else "UNKNOWN" if face_candidates else "FAIL"
        row = {
            "oracle_id": oid,
            "oracle_name": name,
            "source_mask": mask,
            "commander_legality": oracle.get("commander_legality"),
            "type_line": oracle.get("type_line"),
            "production_required": True,
            "exact_script_matches": exact,
            "face_only_candidates": face_candidates,
            "present": source_present,
            "reachability": {
                "decision_path": decision,
                "hidden_info_path": hidden,
                "rng_path": rng,
                "behavior_scripted": behavior,
                "suspicious_markers": suspicious,
            },
            "evidence": {"present": "CODE_DERIVED" if exact else "UNKNOWN"},
        }
        rows.append(row)
        names.append(oid + "\t" + name)
        if source_present != "PASS":
            mapping_gaps.append({
                "oracle_id": oid,
                "oracle_name": name,
                "source_presence": source_present,
                "face_candidates": [
                    {"face_name": x.get("face_name"), "path": x.get("path"), "sha256": x.get("sha256")}
                    for x in face_candidates
                ],
            })
    write_jsonl(out / "prepared.jsonl", rows)
    (out / "names.tsv").write_text("\n".join(names) + ("\n" if names else ""), encoding="utf-8")
    write_json(out / "MAPPING_GAPS.json", {
        "schema": SCHEMA + ".mapping-gaps",
        "count": len(mapping_gaps),
        "rows": mapping_gaps,
        "note": "Source-name mismatch is not promoted. Every canonical Oracle name is still probed through Forge CardDb.",
    })
    summary = {
        "schema": SCHEMA + ".prepare",
        "forge_pin": FORGE_PIN,
        "audit_base_sha": BASE_SHA,
        "ws02_union_sha256": sha256(union_path),
        "ws02_oracle_pin_sha256": sha256(pin_path),
        "oracle_index_sha256": sha256(args.oracle_index),
        "requirement_identity_count": len(rows),
        "exact_present_count": sum(r["present"] == "PASS" for r in rows),
        "face_only_unknown_count": sum(r["present"] == "UNKNOWN" for r in rows),
        "absent_count": sum(r["present"] == "FAIL" for r in rows),
        "loadability_probe_count": len(names),
    }
    write_json(out / "PREPARE_SUMMARY.json", summary)
    return 0


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def semantic_status(required: bool, dependency_ok: bool) -> tuple[str, str]:
    if not required:
        return "NOT_REQUIRED", "CODE_DERIVED"
    if not dependency_ok:
        return "UNKNOWN", "UNKNOWN"
    # Dependency conformance is necessary but not sufficient to prove that this
    # actual identity exercised the path. Never promote path mapping to PASS.
    return "UNKNOWN", "UNKNOWN"


def finalize(args: argparse.Namespace) -> int:
    prepared = load_jsonl(args.prepared)
    load_rows = load_jsonl(args.loadability)
    by_load = {r.get("oracle_id"): r for r in load_rows if isinstance(r.get("oracle_id"), str)}
    deps = read_json(args.dependencies)
    dep = deps.get("dependencies", {})
    ws01_ok = (dep.get("WS01") or {}).get("status") == "PASS"
    ws05_ok = (dep.get("WS05") or {}).get("status") == "PASS"
    ws06_ok = (dep.get("WS06") or {}).get("status") == "PASS"
    ws07_ok = (dep.get("WS07") or {}).get("status") == "PASS"
    ws02_ok = (dep.get("WS02") or {}).get("status") == "PASS"

    out_rows: list[dict[str, Any]] = []
    taxonomy = Counter()
    for base in prepared:
        oid = base["oracle_id"]
        source_present = base["present"]
        load = by_load.get(oid)
        if load is None:
            loadable = "UNKNOWN"
        else:
            loadable = "PASS" if load.get("loadable") is True else "FAIL"
        runtime_exact = bool(
            loadable == "PASS"
            and isinstance(load, dict)
            and load.get("resolved_name") == base["oracle_name"]
        )
        if source_present == "PASS":
            present = "PASS"
            present_ev = base.get("evidence", {}).get("present", "CODE_DERIVED")
        elif runtime_exact:
            present = "PASS"
            present_ev = "TECHNICALLY_CONFORMANT"
        else:
            present = source_present
            present_ev = "UNKNOWN"

        reach = base["reachability"]
        decision_required = bool(reach.get("decision_path"))
        hidden_required = bool(reach.get("hidden_info_path"))
        replay_required = decision_required or bool(reach.get("rng_path"))
        behavior_required = True

        decision_complete, decision_ev = semantic_status(decision_required, ws01_ok)
        hidden_safe, hidden_ev = semantic_status(hidden_required, ws05_ok)
        replay_safe, replay_ev = semantic_status(replay_required, ws06_ok)
        # CardDb load + CardFactory construction are not semantic effect
        # resolution. Construction failure is recorded, but does not by itself
        # prove production execution is unsupported because the probe has no
        # live game/controller.
        executable = "UNKNOWN" if present == "PASS" and loadable == "PASS" else "NOT_TESTED"
        behavior_verified = "UNKNOWN" if behavior_required else "NOT_REQUIRED"

        if present == "FAIL" or loadable == "FAIL":
            classification = "UNSUPPORTED"
        elif present == "UNKNOWN" or loadable == "UNKNOWN":
            classification = "UNKNOWN"
        else:
            required_statuses = [executable, behavior_verified]
            if decision_required:
                required_statuses.append(decision_complete)
            if hidden_required:
                required_statuses.append(hidden_safe)
            if replay_required:
                required_statuses.append(replay_safe)
            classification = "FULL" if all(x == "PASS" for x in required_statuses) and ws07_ok else "PARTIAL"
        assert classification in CLASSIFICATIONS

        if present == "FAIL": taxonomy["CARD_PRESENCE_FAILURE"] += 1
        if present == "UNKNOWN": taxonomy["IDENTITY_TO_SCRIPT_MAPPING_UNKNOWN"] += 1
        if loadable == "FAIL": taxonomy["CARD_LOADABILITY_FAILURE"] += 1
        if loadable == "PASS" and load and load.get("runtime_constructable") is False:
            taxonomy["ENGINE_CONSTRUCTION_PROBE_FAILURE"] += 1
        if executable == "UNKNOWN": taxonomy["EXECUTION_EVIDENCE_MISSING"] += 1
        if decision_required and decision_complete != "PASS": taxonomy["UNSUPPORTED_DECISION_PATH"] += 1
        if hidden_required and hidden_safe != "PASS": taxonomy["HIDDEN_INFO_PATH_UNVERIFIED"] += 1
        if replay_required and replay_safe != "PASS": taxonomy["REPLAY_PATH_UNVERIFIED"] += 1
        if behavior_verified != "PASS": taxonomy["BEHAVIOR_EVIDENCE_MISSING"] += 1

        out_rows.append({
            "schema": SCHEMA + ".identity",
            "oracle_id": oid,
            "oracle_name": base["oracle_name"],
            "source_mask": base["source_mask"],
            "production_required": True,
            "classification": classification,
            "flags": {
                "PRESENT": present,
                "LOADABLE": loadable,
                "EXECUTABLE": executable,
                "DECISION_COMPLETE": decision_complete,
                "HIDDEN_INFO_SAFE": hidden_safe,
                "REPLAY_SAFE": replay_safe,
                "BEHAVIOR_VERIFIED_WHERE_REQUIRED": behavior_verified,
            },
            "source_presence": source_present,
            "required_paths": {
                "decision": decision_required,
                "hidden_info": hidden_required,
                "replay": replay_required,
                "behavior": behavior_required,
            },
            "reachability": reach,
            "loadability_evidence": load,
            "evidence_class": {
                "PRESENT": present_ev,
                "LOADABLE": "TECHNICALLY_CONFORMANT" if loadable == "PASS" else "UNKNOWN",
                "EXECUTABLE": "UNKNOWN",
                "DECISION_COMPLETE": decision_ev,
                "HIDDEN_INFO_SAFE": hidden_ev,
                "REPLAY_SAFE": replay_ev,
                "BEHAVIOR_VERIFIED_WHERE_REQUIRED": "UNKNOWN",
            },
        })

    counts = Counter(r["classification"] for r in out_rows)
    prod_unknown = counts["UNKNOWN"]
    prod_unsupported = counts["UNSUPPORTED"]
    prod_partial = counts["PARTIAL"]
    all_classified = len(out_rows) > 0 and sum(counts.values()) == len(out_rows)
    decision_gate = all(not r["required_paths"]["decision"] or r["flags"]["DECISION_COMPLETE"] == "PASS" for r in out_rows)
    hidden_gate = all(not r["required_paths"]["hidden_info"] or r["flags"]["HIDDEN_INFO_SAFE"] == "PASS" for r in out_rows)
    replay_gate = all(not r["required_paths"]["replay"] or r["flags"]["REPLAY_SAFE"] == "PASS" for r in out_rows)
    behavior_gate = all(r["flags"]["BEHAVIOR_VERIFIED_WHERE_REQUIRED"] == "PASS" for r in out_rows)
    pass_gate = (
        ws02_ok and ws01_ok and ws05_ok and ws06_ok and ws07_ok and all_classified
        and prod_unknown == 0 and prod_unsupported == 0 and prod_partial == 0
        and decision_gate and hidden_gate and replay_gate and behavior_gate
    )
    if not ws07_ok:
        taxonomy["DEPENDENCY_WS07_NOT_COMPLETE"] += 1

    args.out.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.out / "PER_IDENTITY.jsonl", out_rows)
    write_json(args.out / "FAILURE_TAXONOMY.json", dict(sorted(taxonomy.items())))
    summary = {
        "schema": SCHEMA + ".coverage",
        "status": "PASS" if pass_gate else "FAIL_CLOSED",
        "Q6_ACTUAL_CARD_COVERAGE": "PASS" if pass_gate else "NON_PASS",
        "audit_base_sha": BASE_SHA,
        "forge_pin": FORGE_PIN,
        "dependency_evidence": deps,
        "all_requirement_identities_classified": all_classified,
        "requirement_identity_count": len(out_rows),
        "coverage_counts": {k.lower(): counts[k] for k in sorted(CLASSIFICATIONS)},
        "production_reachable_UNKNOWN": prod_unknown,
        "production_reachable_UNSUPPORTED": prod_unsupported,
        "production_reachable_PARTIAL": prod_partial,
        "decision_complete_required_paths": "PASS" if decision_gate else "FAIL",
        "hidden_info_safe_required_paths": "PASS" if hidden_gate else "FAIL",
        "replay_safe_required_paths": "PASS" if replay_gate else "FAIL",
        "behavior_verified_required_paths": "PASS" if behavior_gate else "FAIL",
        "card_name_hacks_added": 0,
        "failure_taxonomy": dict(sorted(taxonomy.items())),
        "evidence_class": ["CODE_DERIVED", "TECHNICALLY_CONFORMANT", "UNKNOWN"],
        "notes": [
            "Exact source presence and Forge CardDb loadability do not prove semantic execution.",
            "Canonical-name CardDb resolution may establish PRESENT for multi-face source-name mismatches, but does not establish EXECUTABLE.",
            "Dependency conformance is necessary but is not silently promoted into per-identity path execution evidence.",
            "Every WS02 requirement identity is treated as production-required for fail-closed Q6 accounting.",
        ],
    }
    write_json(args.out / "ACTUAL_CARD_COVERAGE.runtime.json", summary)
    hash_paths = [args.out / "PER_IDENTITY.jsonl", args.out / "FAILURE_TAXONOMY.json", args.out / "ACTUAL_CARD_COVERAGE.runtime.json"]
    (args.out / "hashes.sha256").write_text("".join(f"{sha256(p)}  {p.name}\n" for p in hash_paths), encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "Q6_ACTUAL_CARD_COVERAGE": summary["Q6_ACTUAL_CARD_COVERAGE"],
        "requirement_identity_count": len(out_rows),
        "coverage_counts": summary["coverage_counts"],
        "failure_taxonomy": summary["failure_taxonomy"],
    }, sort_keys=True))
    return 0 if pass_gate else 3


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("prepare")
    a.add_argument("--ws02", type=Path, required=True)
    a.add_argument("--oracle-index", type=Path, required=True)
    a.add_argument("--forge-cards", type=Path, required=True)
    a.add_argument("--out", type=Path, required=True)
    b = sub.add_parser("finalize")
    b.add_argument("--prepared", type=Path, required=True)
    b.add_argument("--loadability", type=Path, required=True)
    b.add_argument("--dependencies", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    return prepare(args) if args.cmd == "prepare" else finalize(args)


if __name__ == "__main__":
    raise SystemExit(main())
