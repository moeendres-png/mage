#!/usr/bin/env python3
"""Materialize the source-proven AbilityFactory-compatible subset of the 53 G SVar paths.

This is deliberately a runtime-input generator, not qualification evidence. It preserves
both the source-proven parent identity and the target SVar identity. Production execution
must enter through the actual card/root ability or named parent SVar; direct target-SVar
entry remains forbidden.
"""
from __future__ import annotations

import argparse
import base64
import json
import re
from pathlib import Path

API_RE = re.compile(r"(?:^|\s\|\s)(AB|SP|DB)\$\s*([^|]+)")


def fail(msg: str) -> None:
    raise SystemExit("WS33_G_SVAR_AF_CASES=FAIL " + msg)


def b64(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topology", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    topology = json.loads(args.topology.read_text(encoding="utf-8"))
    if topology.get("status") != "PASS" or topology.get("remaining_svar_count") != 53:
        fail("input topology is not the frozen green 53-path frontier")
    cases = [c for c in topology.get("cases", []) if c["selected_parent"]["ability_factory_compatible"]]
    cases.sort(key=lambda c: c["v2_path_id"])
    if len(cases) != 21:
        fail(f"expected 21 AbilityFactory-compatible parent paths, got {len(cases)}")
    if any(c.get("requires_all_selected_parent_entrypoints") for c in cases):
        fail("multi-parent path unexpectedly entered AbilityFactory-compatible subset")

    rows: list[str] = []
    ids: set[str] = set()
    for ordinal, case in enumerate(cases, 1):
        pid = case["v2_path_id"]
        if pid in ids:
            fail(f"duplicate path id {pid}")
        ids.add(pid)
        parent = case["selected_parent"]
        script = parent["script"]
        m = API_RE.search(script)
        if not m:
            fail(f"parent script has no AbilityFactory API token for {pid}")
        source_token = m.group(1) + "$"
        parent_dispatch = m.group(2).strip()
        if not parent_dispatch:
            fail(f"empty parent dispatch for {pid}")
        directive = parent["directive"]
        parent_svar = parent.get("parent_svar") or ""
        if directive == "SVAR" and not parent_svar:
            fail(f"SVAR parent missing parent_svar for {pid}")
        if directive == "ABILITY" and parent_svar:
            fail(f"ABILITY parent unexpectedly names parent_svar for {pid}")
        target_svar = case.get("target_svar") or ""
        target_script = case.get("target_script") or ""
        target_dispatch = case.get("dispatch_token") or ""
        if not target_svar or not target_script or not target_dispatch:
            fail(f"missing target reachability identity for {pid}")
        if not target_script.startswith("DB$"):
            fail(f"AF subset target is not an AbilitySub DB$ path for {pid}")

        fields = [
            ordinal,
            pid,
            case["oracle_identity"],
            case["card_name"],
            parent_dispatch,
            case["implementation_target"],
            case["source_path"],
            int(parent["source_line"]),
            directive,
            source_token,
            int(bool(case["required_hidden_info_evidence"])),
            int(bool(case["required_rng_evidence"])),
            int(bool(case["required_replay_evidence"])),
            int(bool(case["required_decision_evidence"])),
            b64(script),
            parent_svar,
            target_svar,
            target_dispatch,
            b64(target_script),
        ]
        rows.append("\t".join(map(str, fields)))

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(
        "WS33_G_SVAR_AF_CASES=PASS paths=21 entry=SOURCE_PROVEN_PARENT "
        "parent_identity=PRESERVED target_svar_identity=PRESERVED "
        "target_svar_direct_entry=FALSE coverage_mutated=FALSE"
    )


if __name__ == "__main__":
    main()
