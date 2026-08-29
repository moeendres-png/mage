#!/usr/bin/env python3
"""WS10 actual-card behavioral qualification.

Fail-closed classification for the exact WS02 Oracle identity union. Ordinary
Forge declarative card scripts may qualify as CONDITIONAL_FULL only when the
actual Oracle identity is present/loadable, CardFactory can construct it, and
every reached decision/hidden-info/replay contract has a completed dependency
proof. Multi-face identities are resolved generically by an Oracle-derived
front-face alias and are accepted only when Forge CardRules reproduces the
expected Oracle face-name tuple.
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
SCHEMA = "commander-simulator-next.actual-card-behavior.v2"
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
HARD_SUSPICIOUS = {"UNSUPPORTED", "NOT_IMPLEMENTED", "DUMMY", "PLACEHOLDER"}


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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


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
        oracle_declared = None
        for line in text.splitlines():
            if line.startswith("Name:") and name is None:
                name = line[5:].strip()
            elif line.startswith("Oracle:") and oracle_declared is None:
                oracle_declared = line[7:].strip()
        if not name:
            continue
        markers = sorted(k for k, rx in SUSPICIOUS.items() if rx.search(text))
        by_name[name].append({
            "path": str(path.relative_to(cards_root.parent.parent.parent)),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "oracle_declared": oracle_declared,
            "decision_path": bool(DECISION_RE.search(text)),
            "hidden_info_path": bool(HIDDEN_RE.search(text)),
            "rng_path": bool(RNG_RE.search(text)),
            "behavior_scripted": bool(BEHAVIOR_RE.search(text)),
            "suspicious_markers": markers,
            "hard_suspicious_markers": sorted(set(markers) & HARD_SUSPICIOUS),
        })
    return by_name


def oracle_alias_spec(name: str, face_names: Any, exact: list[dict[str, Any]], scripts: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Return a generic, identity-checked CardDb fallback for two-face layouts.

    Forge indexes transform/adventure/reversible-style cards by the main face in
    several layouts while Scryfall's Oracle identity name is `front // back`.
    We never guess from card names: the alias and expected tuple come directly
    from the pinned Oracle index and are enabled only when the Forge source scan
    contains the Oracle front face.
    """
    if exact or not isinstance(face_names, list) or len(face_names) != 2:
        return {"lookup_alias": None, "expected_faces": []}
    if not all(isinstance(x, str) and x and "\t" not in x for x in face_names):
        return {"lookup_alias": None, "expected_faces": []}
    front, back = face_names
    if front not in scripts:
        return {"lookup_alias": None, "expected_faces": []}
    return {"lookup_alias": front, "expected_faces": [front, back]}


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
        if not isinstance(name, str) or not name or "\t" in name:
            raise ValueError(f"missing/invalid canonical Oracle name: {oid}")
        face_names = oracle.get("face_names") or []
        exact = scripts.get(name, [])
        face_candidates: list[dict[str, Any]] = []
        if not exact:
            for face in face_names:
                if isinstance(face, str) and face in scripts:
                    face_candidates.extend({"face_name": face, **x} for x in scripts[face])
        candidates = exact if exact else face_candidates
        suspicious = sorted({m for x in candidates for m in x["suspicious_markers"]})
        hard = sorted({m for x in candidates for m in x["hard_suspicious_markers"]})
        source_present = "PASS" if exact else "UNKNOWN" if face_candidates else "FAIL"
        alias_spec = oracle_alias_spec(name, face_names, exact, scripts)
        row = {
            "oracle_id": oid,
            "oracle_name": name,
            "oracle_face_names": face_names,
            "runtime_lookup": alias_spec,
            "source_mask": mask,
            "commander_legality": oracle.get("commander_legality"),
            "type_line": oracle.get("type_line"),
            "production_required": True,
            "exact_script_matches": exact,
            "face_only_candidates": face_candidates,
            "present": source_present,
            "reachability": {
                "decision_path": any(x["decision_path"] for x in candidates),
                "hidden_info_path": any(x["hidden_info_path"] for x in candidates),
                "rng_path": any(x["rng_path"] for x in candidates),
                "behavior_scripted": any(x["behavior_scripted"] for x in candidates),
                "suspicious_markers": suspicious,
                "hard_suspicious_markers": hard,
            },
            "evidence": {"present": "CODE_DERIVED" if exact else "UNKNOWN"},
        }
        rows.append(row)
        expected = alias_spec["expected_faces"]
        names.append("\t".join([
            oid,
            name,
            alias_spec["lookup_alias"] or "",
            expected[0] if len(expected) == 2 else "",
            expected[1] if len(expected) == 2 else "",
        ]))
        if source_present != "PASS":
            mapping_gaps.append({
                "oracle_id": oid,
                "oracle_name": name,
                "source_presence": source_present,
                "runtime_lookup": alias_spec,
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
        "note": "Multi-face fallback aliases are Oracle-derived and accepted only when Forge CardRules reproduces the expected two-face name tuple.",
    })
    write_json(out / "PREPARE_SUMMARY.json", {
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
        "oracle_alias_probe_count": sum(bool(r["runtime_lookup"]["lookup_alias"]) for r in rows),
        "hard_suspicious_identity_count": sum(bool(r["reachability"]["hard_suspicious_markers"]) for r in rows),
        "loadability_probe_count": len(names),
    })
    return 0


def contract_status(required: bool, dependency_ok: bool) -> tuple[str, str]:
    if not required:
        return "NOT_REQUIRED", "CODE_DERIVED"
    if dependency_ok:
        return "PASS", "TECHNICALLY_CONFORMANT"
    return "UNKNOWN", "UNKNOWN"


def finalize(args: argparse.Namespace) -> int:
    prepared = load_jsonl(args.prepared)
    load_rows = load_jsonl(args.loadability)
    by_load = {r.get("oracle_id"): r for r in load_rows if isinstance(r.get("oracle_id"), str)}
    bootstrap = read_json(args.bootstrap) if args.bootstrap.exists() else {"bootstrap_success": False, "error": "missing bootstrap evidence"}
    deps = read_json(args.dependencies)
    dep = deps.get("dependencies", {})
    ws01_ok = (dep.get("WS01") or {}).get("status") == "PASS"
    ws02_ok = (dep.get("WS02") or {}).get("status") == "PASS"
    ws05_ok = (dep.get("WS05") or {}).get("status") == "PASS"
    ws06_ok = (dep.get("WS06") or {}).get("status") == "PASS"
    ws07_ok = (dep.get("WS07") or {}).get("status") == "PASS"
    bootstrap_ok = bootstrap.get("bootstrap_success") is True

    out_rows: list[dict[str, Any]] = []
    taxonomy = Counter()
    if not bootstrap_ok:
        taxonomy["ENGINE_BOOTSTRAP_FAILURE"] += 1
    if len(load_rows) != len(prepared):
        taxonomy["LOADABILITY_ROW_COUNT_MISMATCH"] += 1

    for base in prepared:
        oid = base["oracle_id"]
        source_present = base["present"]
        load = by_load.get(oid)
        loadable = "UNKNOWN" if load is None else ("PASS" if load.get("loadable") is True and load.get("identity_match") is True else "FAIL")
        runtime_identity_match = bool(loadable == "PASS" and load and load.get("identity_match") is True)

        if source_present == "PASS":
            present = "PASS"
            present_ev = base.get("evidence", {}).get("present", "CODE_DERIVED")
        elif runtime_identity_match:
            present = "PASS"
            present_ev = "TECHNICALLY_CONFORMANT"
        else:
            present = source_present
            present_ev = "UNKNOWN"

        if present == "PASS" and loadable == "PASS" and load and load.get("runtime_constructable") is True and bootstrap_ok:
            executable = "PASS"
            executable_ev = "TECHNICALLY_CONFORMANT"
        elif loadable == "PASS" and load and load.get("runtime_constructable") is False:
            executable = "FAIL"
            executable_ev = "TECHNICALLY_CONFORMANT"
        else:
            executable = "UNKNOWN"
            executable_ev = "UNKNOWN"

        reach = base["reachability"]
        decision_required = bool(reach.get("decision_path"))
        hidden_required = bool(reach.get("hidden_info_path"))
        replay_required = decision_required or bool(reach.get("rng_path"))
        hard_markers = list(reach.get("hard_suspicious_markers") or [])
        dedicated_behavior_required = bool(hard_markers)

        decision_complete, decision_ev = contract_status(decision_required, ws01_ok)
        hidden_safe, hidden_ev = contract_status(hidden_required, ws05_ok)
        replay_safe, replay_ev = contract_status(replay_required, ws06_ok)
        if dedicated_behavior_required:
            behavior_verified = "UNKNOWN"
            behavior_ev = "UNKNOWN"
        else:
            behavior_verified = "NOT_REQUIRED"
            behavior_ev = "CODE_DERIVED"

        statuses = [present, loadable, executable]
        if present == "FAIL" or loadable == "FAIL" or executable == "FAIL":
            classification = "UNSUPPORTED"
        elif "UNKNOWN" in statuses:
            classification = "UNKNOWN"
        else:
            required_ok = (
                (not decision_required or decision_complete == "PASS")
                and (not hidden_required or hidden_safe == "PASS")
                and (not replay_required or replay_safe == "PASS")
                and (not dedicated_behavior_required or behavior_verified == "PASS")
                and ws07_ok
            )
            classification = "CONDITIONAL_FULL" if required_ok else "PARTIAL"
        assert classification in CLASSIFICATIONS

        if present == "FAIL": taxonomy["CARD_PRESENCE_FAILURE"] += 1
        if present == "UNKNOWN": taxonomy["IDENTITY_TO_SCRIPT_MAPPING_UNKNOWN"] += 1
        if loadable == "FAIL": taxonomy["CARD_LOADABILITY_OR_IDENTITY_FAILURE"] += 1
        if loadable == "UNKNOWN": taxonomy["CARD_LOADABILITY_UNKNOWN"] += 1
        if executable == "FAIL": taxonomy["ENGINE_CONSTRUCTION_PROBE_FAILURE"] += 1
        if executable == "UNKNOWN": taxonomy["EXECUTION_EVIDENCE_MISSING"] += 1
        if decision_required and decision_complete != "PASS": taxonomy["DECISION_PATH_UNVERIFIED"] += 1
        if hidden_required and hidden_safe != "PASS": taxonomy["HIDDEN_INFO_PATH_UNVERIFIED"] += 1
        if replay_required and replay_safe != "PASS": taxonomy["REPLAY_PATH_UNVERIFIED"] += 1
        if dedicated_behavior_required and behavior_verified != "PASS": taxonomy["DEDICATED_BEHAVIOR_EVIDENCE_MISSING"] += 1
        if reach.get("suspicious_markers"): taxonomy["SOURCE_SUSPICIOUS_MARKER_WARNING"] += 1

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
            "runtime_lookup": base.get("runtime_lookup"),
            "required_paths": {
                "decision": decision_required,
                "hidden_info": hidden_required,
                "replay": replay_required,
                "dedicated_behavior": dedicated_behavior_required,
            },
            "reachability": reach,
            "loadability_evidence": load,
            "evidence_class": {
                "PRESENT": present_ev,
                "LOADABLE": "TECHNICALLY_CONFORMANT" if loadable in {"PASS", "FAIL"} else "UNKNOWN",
                "EXECUTABLE": executable_ev,
                "DECISION_COMPLETE": decision_ev,
                "HIDDEN_INFO_SAFE": hidden_ev,
                "REPLAY_SAFE": replay_ev,
                "BEHAVIOR_VERIFIED_WHERE_REQUIRED": behavior_ev,
            },
        })

    counts = Counter(r["classification"] for r in out_rows)
    prod_unknown = counts["UNKNOWN"]
    prod_unsupported = counts["UNSUPPORTED"]
    prod_partial = counts["PARTIAL"]
    all_classified = len(out_rows) == len(prepared) and len(out_rows) > 0
    decision_gate = all(not r["required_paths"]["decision"] or r["flags"]["DECISION_COMPLETE"] == "PASS" for r in out_rows)
    hidden_gate = all(not r["required_paths"]["hidden_info"] or r["flags"]["HIDDEN_INFO_SAFE"] == "PASS" for r in out_rows)
    replay_gate = all(not r["required_paths"]["replay"] or r["flags"]["REPLAY_SAFE"] == "PASS" for r in out_rows)
    behavior_gate = all(not r["required_paths"]["dedicated_behavior"] or r["flags"]["BEHAVIOR_VERIFIED_WHERE_REQUIRED"] == "PASS" for r in out_rows)
    pass_gate = (
        bootstrap_ok and ws01_ok and ws02_ok and ws05_ok and ws06_ok and ws07_ok
        and all_classified and len(load_rows) == len(prepared)
        and prod_unknown == 0 and prod_unsupported == 0 and prod_partial == 0
        and decision_gate and hidden_gate and replay_gate and behavior_gate
    )

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
        "bootstrap_evidence": bootstrap,
        "all_requirement_identities_classified": all_classified,
        "requirement_identity_count": len(out_rows),
        "loadability_row_count": len(load_rows),
        "coverage_counts": {k.lower(): counts[k] for k in sorted(CLASSIFICATIONS)},
        "production_reachable_UNKNOWN": prod_unknown,
        "production_reachable_UNSUPPORTED": prod_unsupported,
        "production_reachable_PARTIAL": prod_partial,
        "decision_complete_required_paths": "PASS" if decision_gate else "FAIL",
        "hidden_info_safe_required_paths": "PASS" if hidden_gate else "FAIL",
        "replay_safe_required_paths": "PASS" if replay_gate else "FAIL",
        "behavior_verified_required_paths": "PASS" if behavior_gate else "FAIL",
        "dedicated_behavior_required_count": sum(r["required_paths"]["dedicated_behavior"] for r in out_rows),
        "oracle_alias_resolved_count": sum(bool(r.get("loadability_evidence") and r["loadability_evidence"].get("used_alias")) for r in out_rows),
        "card_name_hacks_added": 0,
        "failure_taxonomy": dict(sorted(taxonomy.items())),
        "evidence_class": ["CODE_DERIVED", "TECHNICALLY_CONFORMANT"],
        "classification_policy": {
            "FULL": "reserved for direct identity-level semantic behavior proof",
            "CONDITIONAL_FULL": "actual Oracle identity is present/loadable/constructable and all reached qualified engine contracts pass; no dedicated card-specific behavior evidence is required",
            "PARTIAL": "runtime identity exists but one required qualified contract is not PASS",
            "UNKNOWN": "required runtime evidence is missing",
            "UNSUPPORTED": "runtime presence/load/identity/construction explicitly failed",
        },
        "notes": [
            "Source presence or parsing alone never establishes coverage.",
            "Multi-face aliases are derived mechanically from pinned Oracle face_names and accepted only when Forge CardRules returns the same ordered face-name tuple.",
            "EXECUTABLE requires successful CardFactory construction after Forge's pinned headless runtime bootstrap.",
            "Decision, hidden-information and replay flags are bound to actual-card source reachability and the completed WS01/WS05/WS06 contracts.",
            "WS07 is a global Commander/multiplayer prerequisite and must independently PASS.",
            "Ordinary declarative scripts are CONDITIONAL_FULL rather than FULL; direct identity-level semantic execution remains the criterion for FULL.",
            "Dedicated behavior evidence is required fail-closed only when the card source advertises an unsupported/not-implemented/dummy/placeholder implementation marker.",
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
    b.add_argument("--bootstrap", type=Path, required=True)
    b.add_argument("--dependencies", type=Path, required=True)
    b.add_argument("--out", type=Path, required=True)
    return p


def main() -> int:
    args = parser().parse_args()
    return prepare(args) if args.cmd == "prepare" else finalize(args)


if __name__ == "__main__":
    raise SystemExit(main())
