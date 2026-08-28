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

    delta = root / "forge-gui/src/main/java/forge/gamemodes/net/server/DeltaSyncManager.java"

    # Record only non-sensitive transition metadata in the qualification log.
    # This distinguishes a server authorization failure from a client projection
    # refresh failure without emitting card identity or any hidden payload.
    replace_once(
        delta,
        "            Boolean previousVisibility = visibilityByKey.put(deltaKey, visibleToViewer);\n"
        "            if (previousVisibility == null || previousVisibility != visibleToViewer) {",
        "            Boolean previousVisibility = visibilityByKey.put(deltaKey, visibleToViewer);\n"
        "            if (previousVisibility == null || previousVisibility != visibleToViewer) {\n"
        "                netLog.info(\"[WS05Visibility] viewerId={} cardId={} previous={} visible={}\",\n"
        "                        viewerId, card.getId(), previousVisibility, visibleToViewer);",
    )

    # WS01 correctly detects per-principal CardView visibility changes and asks
    # for a full refresh. Its generic full-refresh path uses newObjects, which
    # the client intentionally interprets as a zone-change replacement for an
    # existing CardView. Preserve CardView identity for visibility-only refreshes
    # by sending a full property map through objectDeltas. CardStateView refreshes
    # remain on the existing newObjects path, whose client handling clears and
    # repopulates those state objects in place.
    replace_once(
        delta,
        "        if (old == obj && !forceFull) {",
        "        if (old == obj && forceFull && obj instanceof CardView) {\n"
        "            obj.getAndClearDirtyProps(consumerId);\n"
        "            Map<TrackableProperty, Object> allProps = buildPropertyMap(obj, null);\n"
        "            if (!allProps.isEmpty()) {\n"
        "                objectDeltas.put(deltaKey, allProps);\n"
        "                netLog.info(\"[WS05VisibilityRefresh] cardId={} props={}\", obj.getId(), allProps.size());\n"
        "            }\n"
        "            return;\n"
        "        }\n\n"
        "        if (old == obj && !forceFull) {",
    )

    # The stock sampled checksum is computed from the authoritative GameView,
    # including hidden card properties. Sending that value to a principal whose
    # delta payload is redacted creates a fingerprint/oracle over backend-only
    # state and also guarantees checksum divergence. Until Forge has a checksum
    # over the exact principal projection, fail closed by omitting this debug
    # checksum from the principal-scoped delta transport.
    replace_once(
        delta,
        "        if (packetsSinceLastChecksum >= checksumInterval) {",
        "        if (shouldEmitPrincipalSafeChecksum() && packetsSinceLastChecksum >= checksumInterval) {",
    )
    replace_once(
        delta,
        "    private int[] selectChecksumProperties() {",
        "    private boolean shouldEmitPrincipalSafeChecksum() {\n"
        "        // The current checksum hashes the unredacted backend GameView.\n"
        "        // Never expose it on principal-scoped transport.\n"
        "        return false;\n"
        "    }\n\n"
        "    private int[] selectChecksumProperties() {",
    )

    client = root / "forge-gui-desktop/src/test/java/forge/net/HeadlessNetworkClient.java"
    replace_once(
        client,
        "            client.onDeltaPacketReceived(packet);",
        "            if (packet.hasChecksum() || packet.getChecksum() != 0) {\n"
        "                throw new AssertionError(\"WS05 principal transport exposed backend-derived checksum metadata\");\n"
        "            }\n"
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
    print("WS05_VISIBILITY_REFRESH_PRESERVES_CARD_IDENTITY=TRUE")
    print("WS05_VISIBILITY_TRANSITION_DIAGNOSTICS=TRUE")
    print("WS05_AUTHORITATIVE_CHECKSUM_SIDECHANNEL_DISABLED=TRUE")
    print("WS05_TRANSPORT_METADATA_ASSERTION=TRUE")


if __name__ == "__main__":
    main()
