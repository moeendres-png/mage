#!/usr/bin/env python3
"""Harden principal observation fanout and temporary visibility evidence.

The 4P qualification harness intentionally has one local host and three real remote
principals. GameAction.reveal fans public information out to every player controller.
Only remote principals have a decoded RemoteClient projection to qualify. A local host
receiving a non-discretionary REVEAL_OBSERVATION must therefore not fail the rules path
and must not emit synthetic remote evidence. Hidden discretionary Card choices remain
strictly fail-closed unless the bound principal has a RemoteClientGuiGame observation
channel.

ExternalObservationTrace is qualification-only. A server grant is registered before
the first client delta arrives, so the first identity-bearing projection is itself the
positive observation even when no prior client identity state was cached. Initial hidden
state is not emitted as a synthetic revocation.

Pinned Forge also uses PlayerControllerHuman.tempShowCards/endTempShowCards as the real
look-at-cards lifetime for effects such as Dig. Stock Forge changes server-side may-look
permission there but does not itself synchronize a remote principal before an external
decision. Under the strict external boundary, preserve Forge's exact permission lifetime
and add only transport synchronization plus trace evidence: newly hidden cards are
flushed to the bound RemoteClient principal after the grant and flushed again after
revocation. No option, legality, choice, RNG, or rules result is manufactured here.
"""
from pathlib import Path
import argparse


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_OBSERVATION_FANOUT=FAIL {label}: expected anchor once, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    root = args.forge_root.resolve()
    human = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"

    old = '''        if (!(gui instanceof RemoteClientGuiGame remoteGui)) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "hidden authoritative Card choices require RemoteClient principal observation");
        }
'''
    new = '''        if (!(gui instanceof RemoteClientGuiGame remoteGui)) {
            if ("REVEAL_OBSERVATION".equals(decisionKind)) {
                // Public reveal fanout can include the qualification harness' local host.
                // There is no RemoteClient projection to observe for that principal, so
                // claim no positive remote evidence and do not turn presentation fanout
                // into a rules-path failure. Discretionary hidden Card choices below
                // remain fail-closed without a remote principal observation channel.
                return new Ws33ExternalObservation(principal, new CardCollection(), decisionKind);
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "hidden authoritative Card choices require RemoteClient principal observation");
        }
'''
    replace_once(human, old, new, "public reveal host exception")

    old_temp = '''    private final ArrayList<Card> tempShownCards = new ArrayList<>();

    public <T> void tempShow(final Iterable<T> objects) {
        for (final T t : objects) {
            // assume you may see any card passed through here
            if (t instanceof Card c) {
                tempShowCard(c);
            } else if (t instanceof CardView c) {
                tempShowCard(getCard(c));
            }
        }
    }

    private void tempShowCard(final Card c) {
        if (c == null) {
            return;
        }
        tempShownCards.add(c);
        c.addMayLookTemp(player);
    }

    @Override
    public void tempShowCards(final Iterable<Card> cards) {
        for (final Card c : cards) {
            tempShowCard(c);
        }
    }

    @Override
    public void endTempShowCards() {
        if (tempShownCards.isEmpty()) {
            return;
        }

        for (final Card c : tempShownCards) {
            c.removeMayLookTemp(player);
        }
        tempShownCards.clear();
    }
'''
    new_temp = '''    private final ArrayList<Card> tempShownCards = new ArrayList<>();
    private final Set<Integer> ws33TempObservedCardIds = new LinkedHashSet<>();

    private boolean ws33NeedsRemoteTempObservation(final Card card) {
        if (card == null || player == null || !hasExternalDecisionProvider()
                || !(gui instanceof RemoteClientGuiGame)) {
            return false;
        }
        final CardView view = CardView.get(card);
        final PlayerView viewer = PlayerView.get(player);
        return view != null && viewer != null
                && !(view.canBeShownTo(viewer) && view.canFaceDownBeShownTo(viewer));
    }

    private void ws33FlushTempObservationIfNeeded() {
        if (!ws33TempObservedCardIds.isEmpty() && gui instanceof RemoteClientGuiGame remoteGui) {
            remoteGui.updateGameView();
            remoteGui.awaitWs33TransportBarrier();
        }
    }

    public <T> void tempShow(final Iterable<T> objects) {
        for (final T t : objects) {
            // assume you may see any card passed through here
            if (t instanceof Card c) {
                tempShowCard(c);
            } else if (t instanceof CardView c) {
                tempShowCard(getCard(c));
            }
        }
        ws33FlushTempObservationIfNeeded();
    }

    private void tempShowCard(final Card c) {
        if (c == null) {
            return;
        }
        if (ws33NeedsRemoteTempObservation(c)) {
            ExternalObservationTrace.serverGrant(player.getId(), c, "TEMP_SHOW_CARDS");
            ws33TempObservedCardIds.add(c.getId());
        }
        tempShownCards.add(c);
        c.addMayLookTemp(player);
    }

    @Override
    public void tempShowCards(final Iterable<Card> cards) {
        for (final Card c : cards) {
            tempShowCard(c);
        }
        ws33FlushTempObservationIfNeeded();
    }

    @Override
    public void endTempShowCards() {
        if (tempShownCards.isEmpty()) {
            return;
        }

        boolean ws33RevokedObservedCard = false;
        for (final Card c : tempShownCards) {
            if (ws33TempObservedCardIds.remove(c.getId())) {
                ExternalObservationTrace.serverRevoke(player.getId(), c, "TEMP_SHOW_CARDS");
                ws33RevokedObservedCard = true;
            }
            c.removeMayLookTemp(player);
        }
        tempShownCards.clear();
        if (ws33RevokedObservedCard && gui instanceof RemoteClientGuiGame remoteGui) {
            remoteGui.updateGameView();
            remoteGui.awaitWs33TransportBarrier();
        }
        ws33TempObservedCardIds.clear();
    }
'''
    replace_once(human, old_temp, new_temp, "temporary card observation transport")

    trace = root / "forge-gui/src/main/java/forge/gamemodes/match/input/ExternalObservationTrace.java"
    replace_once(
        trace,
        '''                        final Boolean previous = lastIdentity.put(stateKey, identity);
                        if (previous == null || previous == identity) continue;
                        if (identity) {
''',
        '''                        final Boolean previous = lastIdentity.put(stateKey, identity);
                        if (previous != null && previous == identity) continue;
                        if (identity) {
''',
        "initial visible grant",
    )
    replace_once(
        trace,
        '''                        } else {
                            events.add(new Event(sequence.incrementAndGet(), path, "CLIENT_HIDDEN", principalId,
''',
        '''                        } else if (Boolean.TRUE.equals(previous)) {
                            events.add(new Event(sequence.incrementAndGet(), path, "CLIENT_HIDDEN", principalId,
''',
        "initial hidden suppression",
    )

    text = human.read_text(encoding="utf-8")
    if 'if ("REVEAL_OBSERVATION".equals(decisionKind))' not in text:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL reveal exception missing")
    if text.count('hidden authoritative Card choices require RemoteClient principal observation') != 1:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL discretionary fail-closed boundary changed")
    if 'ExternalObservationTrace.serverGrant(player.getId(), c, "TEMP_SHOW_CARDS")' not in text:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL temp-show grant trace missing")
    if 'ExternalObservationTrace.serverRevoke(player.getId(), c, "TEMP_SHOW_CARDS")' not in text:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL temp-show revoke trace missing")
    if text.count('awaitWs33TransportBarrier()') < 4:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL remote temp-show transport barriers missing")
    trace_text = trace.read_text(encoding="utf-8")
    if 'if (previous == null || previous == identity) continue;' in trace_text:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL initial visible grant still suppressed")
    if '} else if (Boolean.TRUE.equals(previous)) {' not in trace_text:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL initial hidden suppression missing")

    print("WS33_OBSERVATION_FANOUT=PASS")
    print("WS33_PUBLIC_REVEAL_LOCAL_HOST_REMOTE_EVIDENCE=0")
    print("WS33_HIDDEN_DISCRETIONARY_CARD_CHOICE_REMOTE_OBSERVATION_REQUIRED=TRUE")
    print("WS33_INITIAL_GRANTED_CARD_VISIBILITY_RECORDED=TRUE")
    print("WS33_INITIAL_HIDDEN_SYNTHETIC_REVOCATION=0")
    print("WS33_TEMP_SHOW_REMOTE_OBSERVATION=PRINCIPAL_SCOPED_DELTA")
    print("WS33_TEMP_SHOW_REMOTE_REVOCATION=PRINCIPAL_SCOPED_DELTA")
    print("WS33_TEMP_SHOW_DECISION_POLICY=UNCHANGED")


if __name__ == "__main__":
    main()
