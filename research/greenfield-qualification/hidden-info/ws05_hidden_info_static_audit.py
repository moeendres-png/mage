#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FORGE_PIN = "8c7e9afb8e6caee88644b94e25da5852e36f8928"
WS01_HEAD = "bf089ea806f54a9bbb64ede205915729e3629684"


def read(root: Path, rel: str) -> str:
    path = root / rel
    if not path.is_file():
        raise SystemExit(f"required file missing: {rel}")
    return path.read_text(encoding="utf-8")


def java_code_without_comments(source: str) -> str:
    """Remove Java line/block comments before source-level privacy assertions.

    Hidden-information audits must inspect executable declarations and calls,
    not fail because a Javadoc comment names a forbidden payload type while
    explicitly documenting that the type is not retained.
    """
    return re.sub(r"/\*.*?\*/|//[^\n]*", "", source, flags=re.DOTALL)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    ap.add_argument("--source-head", required=True)
    ap.add_argument("--source-tree", required=True)
    ap.add_argument("--ws01-head", required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    root = args.forge_root.resolve()
    if args.ws01_head != WS01_HEAD:
        raise SystemExit(f"WS01 dependency drift: {args.ws01_head} != {WS01_HEAD}")

    serializer = read(root, "forge-gui/src/main/java/forge/gamemodes/net/TrackableSerializer.java")
    delta = read(root, "forge-gui/src/main/java/forge/gamemodes/net/server/DeltaSyncManager.java")
    request = read(root, "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionRequest.java")
    tape = read(root, "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalDecisionTape.java")
    tape_code = java_code_without_comments(tape)
    client = read(root, "forge-gui-desktop/src/test/java/forge/net/HeadlessNetworkClient.java")

    assertions = {
        "server_redaction_requires_zone_and_face_visibility": (
            "card.canBeShownTo(viewer) && card.canFaceDownBeShownTo(viewer)" in serializer
        ),
        "unresolved_viewer_fails_closed": (
            "if (card == null || tracker == null || viewerId < 0)" in serializer
            and "return false;" in serializer
        ),
        "full_state_transport_is_viewer_scoped": (
            "redactHiddenInformation" in serializer and "viewerId" in serializer
        ),
        "delta_transport_uses_same_visibility_authority": (
            "TrackableSerializer.canBeShownToViewer" in delta
            and "buildRedactedCardPropertyMap" in delta
        ),
        "visibility_transition_invalidates_projection": (
            "previousVisibility" in delta and "forceFullObjectKeys.add" in delta
        ),
        "visibility_card_refresh_preserves_client_identity": (
            "old == obj && forceFull && obj instanceof CardView" in delta
            and "objectDeltas.put(deltaKey, allProps)" in delta
            and "Visibility refresh in place" in delta
        ),
        "redacted_delta_excludes_identity_fields": all(
            token in delta for token in (
                "TrackableProperty.Name, \"Card\"",
                "TrackableProperty.Owner",
                "TrackableProperty.Controller",
                "TrackableProperty.Zone",
            )
        ) and "buildRedactedCardPropertyMap" in delta,
        "decision_request_is_principal_scoped": (
            "VISIBILITY_PRINCIPAL_ONLY" in request
            and "private final int principalId" in request
            and "private final int actorId" in request
        ),
        "decision_request_does_not_import_game_or_card_views": (
            "import forge.game.GameView" not in request
            and "import forge.game.card.CardView" not in request
        ),
        "decision_tape_omits_semantic_context_and_views": (
            "GameView" not in tape_code
            and "CardView" not in tape_code
            and "getSemanticContext()" not in tape_code
            and "selectedOptionIds" in tape_code
        ),
        "decision_option_ids_are_opaque_typed_membership_tokens": (
            "option id must be type-qualified by entity kind and id" in request
            and "semanticValue = String.valueOf(entityId)" in request
        ),
        "decoded_client_views_are_probed_after_state_application": (
            "Ws05HiddenInfoProbe.observe(client.username, getGameView(), \"delta:" in client
            and "Ws05HiddenInfoProbe.observe(client.username, getGameView(), \"full:" in client
        ),
    }

    status = "PASS" if all(assertions.values()) else "FAIL"
    result = {
        "schema": "commander-simulator-next.ws05-hidden-info-static-audit.v1",
        "source_head": args.source_head,
        "source_tree": args.source_tree,
        "forge_pin": FORGE_PIN,
        "ws01_dependency_head": args.ws01_head,
        "assertions": assertions,
        "status": status,
        "evidence_class": ["CODE_DERIVED", "TECHNICALLY_CONFORMANT"],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "failed": [k for k, v in assertions.items() if not v]}, sort_keys=True))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
