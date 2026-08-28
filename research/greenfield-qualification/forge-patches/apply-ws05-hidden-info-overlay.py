#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one anchor in {path}, found {count}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: apply-ws05-hidden-info-overlay.py <forge-root>")
    root = Path(sys.argv[1]).resolve()

    serializer = root / "forge-gui/src/main/java/forge/gamemodes/net/TrackableSerializer.java"
    replace_once(
        serializer,
        "return viewer != null && card.canBeShownTo(viewer);",
        "return viewer != null && card.canBeShownTo(viewer) && card.canFaceDownBeShownTo(viewer);",
    )

    client = root / "forge-gui-desktop/src/test/java/forge/net/HeadlessNetworkClient.java"
    replace_once(
        client,
        "            client.onDeltaPacketReceived(packet);",
        "            Ws05HiddenInfoProbe.observe(client.username, getGameView(), \"delta:\" + packet.getSequenceNumber());\n"
        "            client.onDeltaPacketReceived(packet);",
    )
    replace_once(
        client,
        "                client.onFullStateSyncReceived(sequenceNumber);",
        "                client.onFullStateSyncReceived(sequenceNumber);\n"
        "                Ws05HiddenInfoProbe.observe(client.username, getGameView(), \"full:\" + sequenceNumber);",
    )

    print("WS05_HIDDEN_INFO_OVERLAY_APPLIED=TRUE")
    print("WS05_FACE_DOWN_VISIBILITY_ENFORCED=TRUE")


if __name__ == "__main__":
    main()
