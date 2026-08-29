#!/usr/bin/env python3
"""Add a WS22-only controlled transport datum injection to the copied WS05 probe.

The production/qualified WS05 source is never edited. This patch is applied only
to the Forge test workspace after the exact WS05 probe has been copied there.
It reuses WS05's private authorized()/identityBearing() detector and counters.
"""
from __future__ import annotations

import argparse
from pathlib import Path

ANCHOR = "    private static boolean authorized(final CardView card, final PlayerView viewer) {\n"
METHOD = r'''    /** WS22-only fault injection at the same CardView/PlayerView boundary used by observe(). */
    public static boolean observeInjectedTransportDatum(final String clientName,
                                                         final CardView card,
                                                         final PlayerView viewer,
                                                         final String source) {
        if (clientName == null || card == null || viewer == null || source == null) {
            throw new IllegalArgumentException("WS22 controlled transport datum requires concrete principal and card view");
        }
        final boolean permitted = authorized(card, viewer);
        final boolean identity = identityBearing(card);
        if (!permitted && identity) {
            transportLeaks.incrementAndGet();
            example("transport:" + source + ":client=" + clientName + ":controlled-cross-principal-datum");
            return true;
        }
        return false;
    }

'''


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("probe", type=Path)
    args = parser.parse_args()
    text = args.probe.read_text(encoding="utf-8")
    if "observeInjectedTransportDatum" in text:
        print("WS22_HIDDEN_PROBE_OVERLAY=ALREADY_APPLIED")
        return 0
    if text.count(ANCHOR) != 1:
        raise SystemExit("exact WS05 probe authorization anchor not found exactly once")
    args.probe.write_text(text.replace(ANCHOR, METHOD + ANCHOR), encoding="utf-8")
    print("WS22_HIDDEN_PROBE_OVERLAY=APPLIED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
