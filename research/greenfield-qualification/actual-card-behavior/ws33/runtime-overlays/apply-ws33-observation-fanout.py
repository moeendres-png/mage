#!/usr/bin/env python3
"""Keep public reveal fanout from claiming nonexistent RemoteClient evidence.

The 4P qualification harness intentionally has one local host and three real remote
principals. GameAction.reveal fans public information out to every player controller.
Only remote principals have a decoded RemoteClient projection to qualify. A local host
receiving a non-discretionary REVEAL_OBSERVATION must therefore not fail the rules path
and must not emit synthetic remote evidence. Hidden discretionary Card choices remain
strictly fail-closed unless the bound principal has a RemoteClientGuiGame observation
channel.
"""
from pathlib import Path
import argparse


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"WS33_OBSERVATION_FANOUT=FAIL expected anchor once, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--forge-root", type=Path, required=True)
    args = ap.parse_args()
    human = args.forge_root.resolve() / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"

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
    replace_once(human, old, new)
    text = human.read_text(encoding="utf-8")
    if 'if ("REVEAL_OBSERVATION".equals(decisionKind))' not in text:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL reveal exception missing")
    if text.count('hidden authoritative Card choices require RemoteClient principal observation') != 1:
        raise SystemExit("WS33_OBSERVATION_FANOUT=FAIL discretionary fail-closed boundary changed")
    print("WS33_OBSERVATION_FANOUT=PASS")
    print("WS33_PUBLIC_REVEAL_LOCAL_HOST_REMOTE_EVIDENCE=0")
    print("WS33_HIDDEN_DISCRETIONARY_CARD_CHOICE_REMOTE_OBSERVATION_REQUIRED=TRUE")


if __name__ == "__main__":
    main()
