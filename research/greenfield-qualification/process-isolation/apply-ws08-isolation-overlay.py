#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS08 expected exactly one anchor in {path}, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("forge_root")
    parser.add_argument("ws08_root")
    args = parser.parse_args()

    forge = Path(args.forge_root).resolve()
    ws08 = Path(args.ws08_root).resolve()
    target_dir = forge / "forge-gui-desktop/src/test/java/forge/net"
    probe = target_dir / "Ws05HiddenInfoProbe.java"
    if not probe.exists():
        raise SystemExit("WS08 requires the read-only WS05 probe to be materialized before its isolation overlay")

    # Extend the already-decoded principal observation probe with one strictly
    # isolation-specific foreign-game sentinel assertion. No WS05 source is
    # modified: this patch exists only in the ephemeral qualification checkout.
    replace_once(
        probe,
        "    private static final AtomicLong replayEvents = new AtomicLong();\n",
        "    private static final AtomicLong replayEvents = new AtomicLong();\n"
        "    private static final AtomicLong ws08CrossGameObservationLeaks = new AtomicLong();\n",
    )
    replace_once(
        probe,
        "        decisionRequests.set(0); replayEvents.set(0);\n",
        "        decisionRequests.set(0); replayEvents.set(0); ws08CrossGameObservationLeaks.set(0);\n",
    )
    replace_once(
        probe,
        "                    for (CardView card : cards) {\n"
        "                        if (card == null) continue;\n",
        "                    for (CardView card : cards) {\n"
        "                        if (card == null) continue;\n"
        "                        if (ws08ContainsForeignSentinel(card)) {\n"
        "                            ws08CrossGameObservationLeaks.incrementAndGet();\n"
        "                            example(\"ws08-cross-game-observation:client=\" + clientName + \" zone=\" + zone);\n"
        "                        }\n",
    )
    replace_once(
        probe,
        "    private static boolean authorized(final CardView card, final PlayerView viewer) {\n",
        "    private static boolean ws08ContainsForeignSentinel(final CardView card) {\n"
        "        final String sentinel = System.getProperty(\"ws08.foreignSentinel\");\n"
        "        if (sentinel == null || sentinel.isBlank() || card == null) return false;\n"
        "        if (sentinel.equals(card.getName()) || sentinel.equals(card.getOracleName())) return true;\n"
        "        try {\n"
        "            final CardView.CardStateView state = card.getCurrentState();\n"
        "            return state != null && (sentinel.equals(state.getName()) || sentinel.equals(state.getOracleName()));\n"
        "        } catch (RuntimeException ignored) {\n"
        "            return false;\n"
        "        }\n"
        "    }\n\n"
        "    public static long ws08CrossGameObservationLeaks() {\n"
        "        return ws08CrossGameObservationLeaks.get();\n"
        "    }\n\n"
        "    private static boolean authorized(final CardView card, final PlayerView viewer) {\n",
    )

    for name in ("Ws08ProcessIsolationWorker.java", "Ws08ProcessIsolationQualificationTest.java"):
        src = ws08 / "research/greenfield-qualification/process-isolation" / name
        dst = target_dir / name
        if dst.exists():
            raise SystemExit(f"WS08 refusing to overwrite unexpected file: {dst}")
        dst.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

    print("WS08_ISOLATION_OVERLAY_APPLIED=TRUE")
    print("WS08_WS05_FOREIGN_OBSERVATION_SENTINEL=TRUE")
    print("WS08_PROCESS_WORKER_INSTALLED=TRUE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
