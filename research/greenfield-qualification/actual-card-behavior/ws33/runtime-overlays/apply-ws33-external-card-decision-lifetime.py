#!/usr/bin/env python3
"""Close Forge temporary-card visibility at the external Card decision boundary.

Pinned Forge can open PlayerControllerHuman.tempShowCards(...) immediately before
chooseEntitiesForEffect(...) and rely on the legacy GUI lifetime to finish before the
caller later invokes endTempShowCards(). In strict external mode the GUI is bypassed.
The authoritative external request is the exact end of the pilot observation lifetime,
so an already-open Forge tempShow scope must be closed when that Card request returns.
The caller's subsequent endTempShowCards() remains an idempotent no-op.

This patch does not create options, choose an option, alter legality, resolve rules, or
change RNG. It only closes an existing Forge may-look scope after the principal has
answered the authoritative Card request.
"""
from pathlib import Path
import argparse


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_EXTERNAL_CARD_DECISION_LIFETIME=FAIL {label}: expected once, got {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    human = args.forge_root.resolve() / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"

    replace_once(
        human,
        '''        private final Player principal;
        private final CardCollection cards;
        private final String decisionKind;
        private Ws33ExternalObservation(final Player principal, final CardCollection cards, final String decisionKind) {
            this.principal = principal;
            this.cards = cards;
            this.decisionKind = decisionKind;
        }
        private boolean isEmpty() { return cards.isEmpty(); }
''',
        '''        private final Player principal;
        private final CardCollection cards;
        private final String decisionKind;
        private final boolean closeForgeTempShow;
        private Ws33ExternalObservation(final Player principal, final CardCollection cards,
                                        final String decisionKind, final boolean closeForgeTempShow) {
            this.principal = principal;
            this.cards = cards;
            this.decisionKind = decisionKind;
            this.closeForgeTempShow = closeForgeTempShow;
        }
        private boolean isEmpty() { return cards.isEmpty() && !closeForgeTempShow; }
''',
        "observation lifetime state",
    )

    replace_once(
        human,
        '''        final CardCollection hidden = new CardCollection();
        if (choices != null) {
            for (final Object choice : choices) {
                if (!(choice instanceof Card card)) continue;
                final CardView view = CardView.get(card);
                final boolean alreadyVisible = view != null
                        && view.canBeShownTo(viewer) && view.canFaceDownBeShownTo(viewer);
                if (!alreadyVisible) hidden.add(card);
            }
        }
        final Ws33ExternalObservation observation = new Ws33ExternalObservation(principal, hidden, decisionKind);
''',
        '''        final CardCollection hidden = new CardCollection();
        boolean hasCardChoice = false;
        if (choices != null) {
            for (final Object choice : choices) {
                if (!(choice instanceof Card card)) continue;
                hasCardChoice = true;
                final CardView view = CardView.get(card);
                final boolean alreadyVisible = view != null
                        && view.canBeShownTo(viewer) && view.canFaceDownBeShownTo(viewer);
                if (!alreadyVisible) hidden.add(card);
            }
        }
        final boolean closeForgeTempShow = hasCardChoice
                && !\"REVEAL_OBSERVATION\".equals(decisionKind)
                && !tempShownCards.isEmpty();
        final Ws33ExternalObservation observation = new Ws33ExternalObservation(
                principal, hidden, decisionKind, closeForgeTempShow);
''',
        "bind existing Forge tempShow to card request",
    )

    # Observation-fanout rewrites the local-host public reveal return after the base
    # observation overlay, so update that constructor independently.
    replace_once(
        human,
        '''                return new Ws33ExternalObservation(principal, new CardCollection(), decisionKind);
''',
        '''                return new Ws33ExternalObservation(principal, new CardCollection(), decisionKind, false);
''',
        "public reveal host constructor",
    )

    replace_once(
        human,
        '''    private void endWs33ExternalCardObservation(final Ws33ExternalObservation observation) {
        if (observation == null || observation.isEmpty()) return;
        if (!(gui instanceof RemoteClientGuiGame remoteGui)) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "hidden Card observation lost RemoteClient transport");
        }
        for (final Card card : observation.cards) {
            card.removeMayLookTemp(observation.principal);
            ExternalObservationTrace.serverRevoke(observation.principal.getId(), card, observation.decisionKind);
        }
        remoteGui.updateGameView();
        remoteGui.awaitWs33TransportBarrier();
    }
''',
        '''    private void endWs33ExternalCardObservation(final Ws33ExternalObservation observation) {
        if (observation == null || observation.isEmpty()) return;
        if (!observation.cards.isEmpty()) {
            if (!(gui instanceof RemoteClientGuiGame remoteGui)) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "hidden Card observation lost RemoteClient transport");
            }
            for (final Card card : observation.cards) {
                card.removeMayLookTemp(observation.principal);
                ExternalObservationTrace.serverRevoke(observation.principal.getId(), card, observation.decisionKind);
            }
            remoteGui.updateGameView();
            remoteGui.awaitWs33TransportBarrier();
        }
        if (observation.closeForgeTempShow) {
            // The strict external request replaced the legacy GUI that bounded this
            // tempShow lifetime. Close it now; the Forge caller's later end is no-op.
            endTempShowCards();
        }
    }
''',
        "close Forge tempShow after authoritative card request",
    )

    text = human.read_text(encoding="utf-8")
    required = [
        "final boolean closeForgeTempShow = hasCardChoice",
        "&& !tempShownCards.isEmpty();",
        "if (observation.closeForgeTempShow)",
        "endTempShowCards();",
    ]
    missing = [token for token in required if token not in text]
    if missing:
        raise SystemExit("WS33_EXTERNAL_CARD_DECISION_LIFETIME=FAIL missing=" + repr(missing))
    print("WS33_EXTERNAL_CARD_DECISION_LIFETIME=PASS")
    print("WS33_FORGE_TEMP_SHOW_CLOSE_BOUNDARY=AUTHORITATIVE_CARD_REQUEST_RETURN")
    print("WS33_FORGE_TEMP_SHOW_RULES_MUTATION=0")
    print("WS33_FORGE_TEMP_SHOW_PILOT_FALLBACK=0")


if __name__ == "__main__":
    main()
