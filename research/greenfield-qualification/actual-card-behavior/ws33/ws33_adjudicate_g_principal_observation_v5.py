#!/usr/bin/env python3
"""WS33 G principal observation v5: shape-aware Manifest adjudication.

v5 preserves the v4 AF summary/lifecycle contract and changes only the source-profile
classification for the pinned-Forge Manifest consumer. The change is intentionally
parameter-shape based, never card-name or path-id based.

Pinned Forge ManifestBaseEffect has materially different shapes:
- `Choices` / `ChoiceZone`: a controller card-selection shape;
- absent/default `Defined`: TopOfLibrary transition;
- explicit other `Defined`: a separately defined-card shape.

The default TopOfLibrary shape does not itself contain a look/card-selection consumer;
it moves the top card face down. A controller's later permission to inspect their own
face-down permanent is a different rules permission and must not be manufactured as a
temporary pre-transition observation. Choice-bearing and other defined shapes remain
fail-closed unless an existing stronger profile (decision/reveal/look) already applies.
"""
from __future__ import annotations

import ws33_adjudicate_g_principal_observation as base
import ws33_adjudicate_g_principal_observation_v4 as v4


_BASE_POSITIVE_PROFILE = base.positive_profile


def positive_profile_v5(api: str, script: str, hidden: bool, decision: bool) -> tuple[str, str]:
    prior = _BASE_POSITIVE_PROFILE(api, script, hidden, decision)
    if api != "Manifest" or prior[0] != "UNKNOWN_HIDDEN_CONSUMER":
        return prior

    params = base.parse_script(script)
    if "Choices" in params or "ChoiceZone" in params:
        return (
            "UNKNOWN_HIDDEN_CONSUMER",
            "pinned-Forge Manifest choice-bearing shape requires explicit principal-observation adjudication",
        )

    defined = params.get("Defined", "TopOfLibrary")
    if defined == "TopOfLibrary":
        return (
            "NEGATIVE_OR_TRANSITION_ONLY",
            "pinned-Forge Manifest default TopOfLibrary face-down transition has no look/card-selection consumer",
        )

    return (
        "UNKNOWN_HIDDEN_CONSUMER",
        f"pinned-Forge Manifest explicit Defined={defined} requires explicit principal-observation adjudication",
    )


def regression_contract() -> None:
    negative = positive_profile_v5(
        "Manifest", "DB$ Manifest | DefinedPlayer$ TargetedController", True, False
    )
    assert negative[0] == "NEGATIVE_OR_TRANSITION_ONLY", negative

    explicit_defined = positive_profile_v5(
        "Manifest", "DB$ Manifest | Defined$ Targeted", True, False
    )
    assert explicit_defined[0] == "UNKNOWN_HIDDEN_CONSUMER", explicit_defined

    choice_zone = positive_profile_v5(
        "Manifest", "DB$ Manifest | ChoiceZone$ Library", True, False
    )
    assert choice_zone[0] == "UNKNOWN_HIDDEN_CONSUMER", choice_zone

    decision = positive_profile_v5(
        "Manifest", "DB$ Manifest | ChoiceZone$ Library", True, True
    )
    assert decision[0] == "POSITIVE_TEMPORARY_REQUIRED", decision

    scry = positive_profile_v5("Scry", "DB$ Scry | Defined$ You | ScryNum$ X", True, False)
    assert scry[0] == "POSITIVE_TEMPORARY_REQUIRED", scry

    nonhidden = positive_profile_v5("Manifest", "DB$ Manifest", False, False)
    assert nonhidden[0] == "NONE_REQUIRED", nonhidden


def main() -> None:
    regression_contract()
    base.positive_profile = positive_profile_v5
    v4.main()


if __name__ == "__main__":
    main()
