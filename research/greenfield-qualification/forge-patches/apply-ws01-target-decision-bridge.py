#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-target-decision-bridge.py <forge-root>")
root = Path(sys.argv[1]).resolve()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one target bridge anchor in {path}, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


controller = root / "forge-gui/src/main/java/forge/player/PlayerControllerHuman.java"
replace_once(controller, '        rejectExternalDecision("TARGET_SELECTION");\n', '')
replace_once(controller, '        rejectExternalDecision("TARGET_RESELECTION");\n', '')

target_selection = root / "forge-gui/src/main/java/forge/player/TargetSelection.java"
replace_once(
    target_selection,
    '''        PlayerView playerView = controller.getLocalPlayerView();
        PlayerZoneUpdates playerZoneUpdates = controller.getGui().openZones(playerView, validTargets.stream().map(c -> c.getZone().getZoneType()).collect(Collectors.toSet()), playersWithValidTargets, true);
        if (!zones.contains(ZoneType.Stack)) {
            InputSelectTargets inp = new InputSelectTargets(controller, validTargets, ability, mandatory, numTargets, divisionValues, filter, mustTargetFiltered);
            inp.showAndWait();
            choiceResult = !inp.hasCancelled();
            bTargetingDone = inp.hasPressedOk();
            controller.getGui().restoreOldZones(playerView, playerZoneUpdates);
''',
    '''        PlayerView playerView = controller.getLocalPlayerView();
        final boolean strictExternal = controller.hasExternalDecisionProvider();
        PlayerZoneUpdates playerZoneUpdates = strictExternal
                ? new PlayerZoneUpdates()
                : controller.getGui().openZones(playerView,
                        validTargets.stream().map(c -> c.getZone().getZoneType()).collect(Collectors.toSet()),
                        playersWithValidTargets, true);
        if (!zones.contains(ZoneType.Stack)) {
            InputSelectTargets inp = new InputSelectTargets(controller, validTargets, ability, mandatory, numTargets, divisionValues, filter, mustTargetFiltered);
            if (strictExternal) {
                inp.driveExternal();
            } else {
                inp.showAndWait();
            }
            choiceResult = !inp.hasCancelled();
            bTargetingDone = inp.hasPressedOk();
            if (!strictExternal) {
                controller.getGui().restoreOldZones(playerView, playerZoneUpdates);
            }
''')

inp = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSelectTargets.java"
replace_once(
    inp,
    '''    @Override
    public String getActivateAction(final Card card) {
''',
    '''    private boolean canExternalSelectCard(final Card card) {
        if (targets.contains(card)) {
            return true; // authoritative toggle removes an already selected target
        }
        if (!choices.contains(card)) {
            return false;
        }
        if (sa.isSpell() && sa.getHostCard().isAura()
                && card.cantBeAttachedMsg(sa.getHostCard(), sa) != null) {
            return false;
        }
        if (!card.canBeTargetedBy(sa)) {
            return false;
        }
        if (tgt.isWithoutSameCreatureType() && lastTarget != null && card.sharesCreatureTypeWith(lastTarget)) {
            return false;
        }
        if (tgt.isWithSameCreatureType() && lastTarget != null && !card.sharesCreatureTypeWith(lastTarget)) {
            return false;
        }
        if (tgt.isWithSameCardType() && lastTarget != null && !card.sharesCardTypeWith(lastTarget)) {
            return false;
        }
        if (sa.hasParam("MaxTotalTargetCMC")) {
            final int maxTotalCMC = tgt.getMaxTotalCMC(sa.getHostCard(), sa);
            if (maxTotalCMC > 0) {
                int soFar = Aggregates.sum(sa.getTargets().getTargetCards(), Card::getCMC);
                if (!sa.isTargeting(card)) {
                    soFar += card.getCMC();
                }
                if (soFar > maxTotalCMC) {
                    return false;
                }
            }
        }
        if (sa.hasParam("MaxTotalTargetPower")) {
            final int maxTotalPower = tgt.getMaxTotalPower(sa.getHostCard(), sa);
            if (maxTotalPower > 0) {
                int soFar = Aggregates.sum(sa.getTargets().getTargetCards(), Card::getNetPower);
                if (!sa.isTargeting(card)) {
                    soFar += card.getNetPower();
                }
                if (soFar > maxTotalPower) {
                    return false;
                }
            }
        }
        if (tgt.isSameController()) {
            for (final GameObject target : targets) {
                if (target instanceof Card c && c.getController() != card.getController()) {
                    return false;
                }
            }
        }
        if (tgt.isDifferentControllers() || tgt.isForEachPlayer()) {
            for (final GameObject target : targets) {
                if (target instanceof Card c && c.getController() == card.getController()) {
                    return false;
                }
            }
        }
        if (tgt.isEqualToughness()) {
            for (final GameObject target : targets) {
                if (target instanceof Card c && c.getNetToughness() != card.getNetToughness()) {
                    return false;
                }
            }
        }
        if (tgt.isDifferentCMC()) {
            for (final GameObject target : targets) {
                if (target instanceof Card c && c.getCMC() == card.getCMC()) {
                    return false;
                }
            }
        }
        if (tgt.isDifferentNames()) {
            for (final GameObject target : targets) {
                if (target instanceof Card c && c.sharesNameWith(card)) {
                    return false;
                }
            }
        }
        return true;
    }

    private boolean canExternalSelectPlayer(final Player player) {
        if (targets.contains(player)) {
            return true;
        }
        if (player == null || player.hasLost()) {
            return false;
        }
        if (sa.isSpell() && sa.getHostCard().isAura() && !player.canBeAttached(sa.getHostCard(), sa)) {
            return false;
        }
        if (!sa.canTarget(player) || mustTargetFiltered) {
            return false;
        }
        return filter == null || filter.test(player);
    }

    public List<String> getExternalActionTokens() {
        final List<String> actions = new ArrayList<>();
        final boolean divisionComplete = divisionValues == null || divisionValues.isEmpty();
        if (sa.isMinTargetChosen() && (numTargets == null || targets.size() == numTargets) && divisionComplete) {
            actions.add("DONE");
        }
        if (!mandatory) {
            actions.add("CANCEL");
        }
        for (final Card card : choices) {
            if (canExternalSelectCard(card)) {
                actions.add("CARD:" + card.getId());
            }
        }
        for (final Player candidate : getController().getGame().getPlayers()) {
            if (canExternalSelectPlayer(candidate)) {
                actions.add("PLAYER:" + candidate.getId());
            }
        }
        return actions;
    }

    public void applyExternalAction(final String action) {
        if ("DONE".equals(action)) {
            final boolean divisionComplete = divisionValues == null || divisionValues.isEmpty();
            if (!sa.isMinTargetChosen() || (numTargets != null && targets.size() != numTargets) || !divisionComplete) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "target selection is not complete");
            }
            onOk();
            return;
        }
        if ("CANCEL".equals(action)) {
            if (mandatory) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.CANCEL_NOT_ALLOWED, "mandatory target selection cannot cancel");
            }
            onCancel();
            return;
        }
        if (action != null && action.startsWith("CARD:")) {
            final int id;
            try {
                id = Integer.parseInt(action.substring("CARD:".length()));
            } catch (RuntimeException error) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "invalid target card token");
            }
            for (final Card card : choices) {
                if (card.getId() == id && canExternalSelectCard(card)) {
                    onCardSelected(card, null, null);
                    return;
                }
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "stale target card token");
        }
        if (action != null && action.startsWith("PLAYER:")) {
            final int id;
            try {
                id = Integer.parseInt(action.substring("PLAYER:".length()));
            } catch (RuntimeException error) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "invalid target player token");
            }
            for (final Player candidate : getController().getGame().getPlayers()) {
                if (candidate.getId() == id && canExternalSelectPlayer(candidate)) {
                    onPlayerSelected(candidate, null);
                    return;
                }
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "stale target player token");
        }
        throw new ExternalDecisionValidationException(
                ExternalDecisionValidationException.Code.ILLEGAL_OPTION, "unknown target action token");
    }

    public void driveExternal() {
        while (!bCancel && !bOk) {
            final List<String> actions = getExternalActionTokens();
            if (actions.isEmpty()) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "TARGET_SELECTION has no authoritative transition");
            }
            final String action = getController().chooseExternalUiOptions(actions, 1, 1, false, false,
                    "TARGET_SELECTION", value -> value).get(0);
            applyExternalAction(action);
        }
    }

    @Override
    public String getActivateAction(final Card card) {
''')

print("WS01_TARGET_DECISION_BRIDGE_APPLIED=TRUE")
