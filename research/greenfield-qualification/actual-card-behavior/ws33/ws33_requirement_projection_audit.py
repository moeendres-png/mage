#!/usr/bin/env python3
"""Audit WS33 evidence requirements against pinned Forge, conservatively.

Generation 2 froze path identity correctly, but its required_* evidence flags inherited
class-wide WS26 signals. This audit is deliberately non-mutating. It currently owns
one source-proven correction scope only: HIDDEN_RNG_REPLAY (WS33G). Every non-G path
is preserved byte-for-byte at the requirement level until an equally strong consumer
model exists for that family.

The G policy is derived from the actual pinned Forge effect implementations and active
path selectors. It therefore distinguishes, for example:
* Scry/Surveil: hidden information + player arrangement decision, no intrinsic RNG.
* FlipCoin: RNG plus a heads/tails call unless NoCall is active.
* Dig: private-zone handling, selector-dependent card/order choices, RNG only when an
  active RandomChange/RestRandomOrder branch requests it.
* Discover: public reveal from a hidden library, cast-vs-hand choice, random rest order.
* DigUntil: optional/attachment/target choices plus ordering only when the actual
  revealed destination is a known zone (or a non-random library reorder); RNG only for
  Shuffle or RevealRandomOrder.
No PASS path may acquire a stronger requirement through this audit; that fails closed.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
G_OWNER = "HIDDEN_RNG_REPLAY"
REQS = (
    ("decision", "required_decision_evidence"),
    ("rng", "required_rng_evidence"),
    ("hidden", "required_hidden_info_evidence"),
    ("replay", "required_replay_evidence"),
)

G_POLICY_TARGETS = {
    "forge.game.ability.effects.ClashEffect",
    "forge.game.ability.effects.DigEffect",
    "forge.game.ability.effects.DigUntilEffect",
    "forge.game.ability.effects.DiscoverEffect",
    "forge.game.ability.effects.FlipCoinEffect",
    "forge.game.ability.effects.ManifestEffect",
    "forge.game.ability.effects.PeekAndRevealEffect",
    "forge.game.ability.effects.RearrangeTopOfLibraryEffect",
    "forge.game.ability.effects.RevealEffect",
    "forge.game.ability.effects.RevealHandEffect",
    "forge.game.ability.effects.ScryEffect",
    "forge.game.ability.effects.ShuffleEffect",
    "forge.game.ability.effects.SurveilEffect",
    "forge.game.ability.effects.TwoPilesEffect",
}

# Anchors are not used as semantic rules; they pin the policy to the expected Forge
# implementation shape and fail closed if the audited pin/source no longer matches.
SOURCE_ANCHORS = {
    "forge.game.ability.effects.ScryEffect": ("getAction().scry(",),
    "forge.game.ability.effects.SurveilEffect": (".surveil(",),
    "forge.game.ability.effects.FlipCoinEffect": ("chooseBinary(", "MyRandom.getRandom()"),
    "forge.game.ability.effects.ShuffleEffect": (".shuffle(sa)",),
    "forge.game.ability.effects.PeekAndRevealEffect": ("getController().reveal(", "RevealOptional"),
    "forge.game.ability.effects.RevealHandEffect": ("ZoneType.Hand", "confirmAction("),
    "forge.game.ability.effects.RevealEffect": ("chooseCardsToRevealFromHand(", "Aggregates.random("),
    "forge.game.ability.effects.DigEffect": ("chooseEntitiesForEffect(", "RestRandomOrder", "CardLists.shuffle("),
    "forge.game.ability.effects.DiscoverEffect": ("confirmAction(", "CardLists.shuffle("),
    "forge.game.ability.effects.DigUntilEffect": ("orderMoveToZoneList(", "RevealRandomOrder", "MyRandom.getRandom()"),
    "forge.game.ability.effects.RearrangeTopOfLibraryEffect": ("orderMoveToZoneList(", "MayShuffle"),
    "forge.game.ability.effects.ManifestEffect": ("extends ManifestBaseEffect",),
    "forge.game.ability.effects.ClashEffect": ("willPutCardOnTop(",),
    "forge.game.ability.effects.TwoPilesEffect": ("chooseCardsForEffect(", "chooseCardsPile("),
}


def load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit("WS33_REQUIREMENT_PROJECTION_AUDIT=FAIL " + msg)


def class_source(target: str, root: Path) -> Path | None:
    base = target.split("#", 1)[0]
    if not base.startswith("forge."):
        return None
    rel = Path(*base.split(".")).with_suffix(".java")
    for module in ("forge-game", "forge-core", "forge-gui", "forge-ai"):
        path = root / module / "src/main/java" / rel
        if path.is_file():
            return path
    return None


def raw_selectors(path: dict[str, Any]) -> dict[str, str]:
    profile = path.get("semantic_selector_profile") or {}
    selectors = profile.get("selectors") or {}
    if not isinstance(selectors, dict):
        return {}
    return {str(key): str(value) for key, value in selectors.items()}


def current_requirements(path: dict[str, Any]) -> dict[str, bool]:
    return {title: bool(path.get(field)) for title, field in REQS}


def truthy(selectors: dict[str, str], key: str) -> bool:
    if key not in selectors:
        return False
    return selectors[key].strip().lower() not in {"", "false", "no", "none", "0"}


def is_value(selectors: dict[str, str], key: str, value: str) -> bool:
    return selectors.get(key, "").strip().lower() == value.lower()


def private_zone_value(value: str) -> bool:
    tokens = {token.lower() for token in re.split(r"[^A-Za-z]+", value) if token}
    return bool(tokens & {"library", "hand"})


def known_zone_value(value: str) -> bool:
    # Pinned ZoneType marks these as hidden. DigUntil only asks the controller to
    # order revealed cards when finalDest.isKnown(), except for an explicitly
    # non-random Library destination handled by the adjacent source condition.
    hidden = {
        "hand", "library", "sideboard", "schemedeck", "planardeck",
        "attractiondeck", "contraptiondeck", "subgame", "extrahand", "none",
    }
    return value.strip().lower() not in hidden


def source_proof(target: str, forge_root: Path) -> dict[str, Any]:
    source = class_source(target, forge_root)
    require(source is not None, "missing pinned Forge source for G target " + target)
    text = source.read_text(encoding="utf-8", errors="replace")
    anchors = SOURCE_ANCHORS[target]
    missing = [anchor for anchor in anchors if anchor not in text]
    require(not missing, f"pinned Forge source anchor drift target={target} missing={missing}")
    return {
        "forge_source_path": source.relative_to(forge_root).as_posix(),
        "forge_source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "verified_source_anchors": list(anchors),
    }


def project_g(path: dict[str, Any], forge_root: Path) -> tuple[dict[str, bool], dict[str, Any]]:
    target = path["implementation_target"]
    require(target in G_POLICY_TARGETS, "unmodeled G implementation target " + target)
    selectors = raw_selectors(path)
    simple = target.rsplit(".", 1)[-1]
    proof = source_proof(target, forge_root)

    decision = False
    rng = False
    hidden = False
    reasons: list[str] = []

    if simple == "ScryEffect":
        decision = True
        hidden = True
        reasons += ["GameAction.scry delegates top/bottom arrangement to PlayerController",
                    "scry inspects a hidden library segment"]
    elif simple == "SurveilEffect":
        decision = True
        hidden = True
        reasons += ["Player.surveil delegates graveyard/top arrangement to PlayerController",
                    "surveil inspects a hidden library segment"]
    elif simple == "FlipCoinEffect":
        rng = True
        decision = not truthy(selectors, "NoCall")
        reasons.append("FlipCoinEffect consumes MyRandom")
        if decision:
            reasons.append("active path calls heads/tails unless NoCall is present")
    elif simple == "ShuffleEffect":
        rng = True
        decision = truthy(selectors, "Optional") or truthy(selectors, "ValidTgts")
        reasons.append("ShuffleEffect delegates library randomization to Player.shuffle")
        if decision:
            reasons.append("active Optional/target selector requires player choice")
    elif simple == "PeekAndRevealEffect":
        hidden = True
        decision = truthy(selectors, "RevealOptional") or truthy(selectors, "ValidTgts")
        reasons.append("effect reads a library/private-zone segment before any reveal")
        if decision:
            reasons.append("active RevealOptional or target selector requires player choice")
    elif simple == "RevealHandEffect":
        hidden = True
        decision = truthy(selectors, "Optional") or truthy(selectors, "ValidTgts")
        reasons.append("effect reads a player's hidden hand")
        if decision:
            reasons.append("active Optional or target selector requires player choice")
    elif simple == "RevealEffect":
        hidden = True
        rng = truthy(selectors, "Random")
        deterministic_selection = (
            rng
            or truthy(selectors, "RevealDefined")
            or truthy(selectors, "RevealAllValid")
        )
        decision = (
            truthy(selectors, "ValidTgts")
            or not deterministic_selection
            or truthy(selectors, "AnyNumber")
            or truthy(selectors, "Optional")
        )
        reasons.append("RevealEffect reads cards from a hidden hand")
        if rng:
            reasons.append("active Random branch uses Forge random selection")
        if decision:
            reasons.append("active branch requires target or chooseCardsToRevealFromHand")
    elif simple == "DigEffect":
        source_zone = selectors.get("SourceZone", "Library")
        hidden = private_zone_value(source_zone)
        rng = truthy(selectors, "RandomChange") or truthy(selectors, "RestRandomOrder")
        change_all = is_value(selectors, "ChangeNum", "All")
        decision = not change_all
        decision = decision or any(
            truthy(selectors, key)
            for key in (
                "PromptToSkipOptionalAbility", "Choser", "Chooser", "ForEachColorPair",
                "WithDifferentPowers", "WithTotalCMC", "DestZone2Optional", "ValidTgts",
            )
        )
        if change_all and selectors.get("DestinationZone", "").lower() in {"library", "battlefield"}:
            decision = True
        if hidden:
            reasons.append("active Dig source zone is private")
        if not change_all:
            reasons.append("active Dig branch selects some/any cards rather than ChangeNum=All")
        if rng:
            reasons.append("active RandomChange/RestRandomOrder branch consumes Forge RNG")
        if decision and change_all:
            reasons.append("active selector still reaches a controller/ordering transition")
    elif simple == "DiscoverEffect":
        decision = True
        rng = True
        hidden = True
        reasons += [
            "discover reveals from a previously hidden library frontier",
            "found card takes an authoritative cast-vs-hand/player ability choice",
            "rest is explicitly moved to library in random order",
        ]
    elif simple == "DigUntilEffect":
        dig_zone = selectors.get("DigZone", "Library")
        hidden = private_zone_value(dig_zone)
        shuffle = truthy(selectors, "Shuffle")
        reveal_random = truthy(selectors, "RevealRandomOrder")
        rng = shuffle or reveal_random
        decision = any(
            truthy(selectors, key)
            for key in ("Optional", "OptionalFoundMove", "AttachedTo", "ValidTgts")
        )
        if not truthy(selectors, "NoMoveRevealed"):
            revealed_dest = selectors.get("RevealedDestination", "")
            order_revealed = bool(revealed_dest) and (
                known_zone_value(revealed_dest)
                or (revealed_dest.strip().lower() == "library" and not shuffle and not reveal_random)
            )
            decision = decision or order_revealed
            if order_revealed:
                reasons.append("active revealed destination reaches DigUntil orderMoveToZoneList when multiple cards are revealed")
        if hidden:
            reasons.append("active DigUntil source zone is private")
        if rng:
            reasons.append("active Shuffle/RevealRandomOrder branch consumes Forge RNG")
        if decision and not any("orderMoveToZoneList" in reason for reason in reasons):
            reasons.append("active path reaches optional/target/attachment choice")
    elif simple == "RearrangeTopOfLibraryEffect":
        decision = True
        hidden = True
        rng = truthy(selectors, "MayShuffle")
        reasons += ["top-of-library order is chosen by PlayerController",
                    "rearrangement exposes a hidden library segment to the entitled player"]
        if rng:
            reasons.append("MayShuffle can invoke Player.shuffle")
    elif simple == "ManifestEffect":
        choice_zone = selectors.get("ChoiceZone")
        from_default_library = "Choices" not in selectors and "ChoiceZone" not in selectors
        hidden = from_default_library or (choice_zone is not None and private_zone_value(choice_zone))
        decision = (
            truthy(selectors, "Choices")
            or truthy(selectors, "ChoiceZone")
            or truthy(selectors, "ValidTgts")
        )
        rng = truthy(selectors, "Shuffle")
        if hidden:
            reasons.append("manifest source is a private hand/library selection or top-of-library card")
        if decision:
            reasons.append("ManifestBaseEffect calls chooseCardsForEffect for active Choices/ChoiceZone")
        if rng:
            reasons.append("ManifestBaseEffect active Shuffle branch consumes Forge RNG")
    elif simple == "ClashEffect":
        decision = True
        hidden = True
        reasons += [
            "clash may select an opponent and each clashing player chooses top vs bottom",
            "top cards originate in hidden libraries before the public reveal",
        ]
    elif simple == "TwoPilesEffect":
        decision = True
        rng = False
        zone = selectors.get("Zone", "")
        hidden = private_zone_value(zone) or truthy(selectors, "FaceDown")
        hidden = hidden or current_requirements(path)["hidden"]
        reasons.append("TwoPilesEffect asks a separator to divide cards and a chooser to choose a pile")
        if hidden:
            reasons.append("active/source-proven pile contents can contain principal-private cards")
    else:  # pragma: no cover - guarded by G_POLICY_TARGETS
        raise AssertionError(simple)

    replay = decision or rng
    projected = {"decision": decision, "rng": rng, "hidden": hidden, "replay": replay}
    return projected, {
        "basis": "PINNED_FORGE_G_EFFECT_BRANCH_POLICY_V2",
        "active_selectors": dict(sorted(selectors.items())),
        "projection_reasons": reasons,
        **proof,
    }


def project(path: dict[str, Any], forge_root: Path) -> tuple[dict[str, bool], dict[str, Any]]:
    current = current_requirements(path)
    if path.get("owner_family") != G_OWNER:
        return current, {
            "basis": "PRESERVE_NON_G_UNTIL_SOURCE_PROVEN_CONSUMER_MODEL",
            "active_selectors": dict(sorted(raw_selectors(path).items())),
            "projection_reasons": ["no requirement mutation is authorized outside WS33G by this audit version"],
        }
    return project_g(path, forge_root)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--coverage", type=Path, required=True)
    ap.add_argument("--forge-root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    head = subprocess.check_output(
        ["git", "-C", str(args.forge_root), "rev-parse", "HEAD"], text=True
    ).strip()
    require(head == PIN, "Forge pin mismatch")

    manifest = load(args.manifest)
    coverage = load(args.coverage)
    paths = manifest["paths"]
    status = {row["effective_v2_path_id"]: row["status"] for row in coverage["paths"]}
    require(set(status) == {path["v2_path_id"] for path in paths}, "manifest/coverage mismatch")

    g_paths = [path for path in paths if path.get("owner_family") == G_OWNER]
    require(len(g_paths) == 81, f"expected authoritative G frontier cardinality 81, got {len(g_paths)}")
    require(
        {path["implementation_target"] for path in g_paths} == G_POLICY_TARGETS,
        "G implementation target set changed; source policy must be re-adjudicated",
    )

    rows = []
    removals = collections.Counter()
    upgrades = collections.Counter()
    changes_by_owner = collections.Counter()
    pass_upgrades: list[str] = []
    changed_unknown = 0
    preserved_non_g = 0

    for path in paths:
        pid = path["v2_path_id"]
        current = current_requirements(path)
        projected, detail = project(path, args.forge_root)
        removed = sorted(key for key in current if current[key] and not projected[key])
        added = sorted(key for key in current if not current[key] and projected[key])
        if path.get("owner_family") != G_OWNER:
            preserved_non_g += 1
            require(not removed and not added, "non-G requirement changed unexpectedly: " + pid)
        for key in removed:
            removals[key] += 1
        for key in added:
            upgrades[key] += 1
        if removed or added:
            changes_by_owner[str(path.get("owner_family"))] += 1
        if status[pid] == "PASS" and added:
            pass_upgrades.append(pid)
        if status[pid] == "UNKNOWN" and (removed or added):
            changed_unknown += 1
        if removed or added:
            rows.append({
                "effective_path_id": pid,
                "status": status[pid],
                "owner_family": path["owner_family"],
                "implementation_target": path["implementation_target"],
                "current": current,
                "projected": projected,
                "removal_candidates": removed,
                "upgrade_candidates": added,
                "classification": (
                    "SOURCE_PROVEN_OVERPROJECTION" if removed and not added
                    else "SOURCE_PROVEN_UNDERPROJECTION" if added and not removed
                    else "SOURCE_PROVEN_MIXED_REPROJECTION"
                ),
                **detail,
            })

    result = {
        "schema": "commander-simulator-next.ws33-requirement-projection-audit.v4",
        "forge_pin": PIN,
        "manifest_sha256": hashlib.sha256(args.manifest.read_bytes()).hexdigest(),
        "effective_path_count": len(paths),
        "unknown_path_count": sum(value == "UNKNOWN" for value in status.values()),
        "authoritative_projection_scope": G_OWNER,
        "authoritative_projection_scope_path_count": len(g_paths),
        "preserved_non_scope_path_count": preserved_non_g,
        "changed_unknown_path_count": changed_unknown,
        "candidate_row_count": len(rows),
        "changed_path_counts_by_owner": dict(changes_by_owner),
        "removal_candidate_counts": dict(removals),
        "upgrade_candidate_counts": dict(upgrades),
        "pass_upgrade_candidate_count": len(pass_upgrades),
        "pass_upgrade_candidate_ids": pass_upgrades,
        "status": "PASS" if not pass_upgrades else "FAIL_CLOSED_PASS_REQUIREMENT_UPGRADE",
        "disposition": "AUDIT_ONLY_NO_MANIFEST_MUTATION",
        "candidates": rows,
    }
    write(args.out, result)
    if pass_upgrades:
        first = next(row for row in rows if row["effective_path_id"] == pass_upgrades[0])
        print("FIRST_PASS_UPGRADE_CANDIDATE=" + json.dumps(first, sort_keys=True))
    require(not pass_upgrades, "projection would strengthen existing PASS requirements")
    print(json.dumps({
        "WS33_REQUIREMENT_PROJECTION_AUDIT": "PASS",
        "schema": result["schema"],
        "paths": len(paths),
        "scope": G_OWNER,
        "scope_paths": len(g_paths),
        "changed_unknown": changed_unknown,
        "candidate_rows": len(rows),
        "removals": dict(removals),
        "upgrades": dict(upgrades),
        "preserved_non_scope": preserved_non_g,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
