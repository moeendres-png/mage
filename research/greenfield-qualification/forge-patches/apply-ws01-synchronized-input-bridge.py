#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-synchronized-input-bridge.py <forge-root>")
root = Path(sys.argv[1]).resolve()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one synchronized-input anchor in {path}, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


entities = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSelectEntitiesFromList.java"
replace_once(
    entities,
    '''    @Override
    public final Collection<T> getSelected() {
''',
    '''    public void driveExternal() {
        while (true) {
            final List<String> actions = new ArrayList<>();
            if (hasEnoughTargets()) {
                actions.add("DONE");
            }
            if (allowCancel) {
                actions.add("CANCEL");
            }
            for (final T entity : validChoices) {
                actions.add("ENTITY:" + ExternalDecisionRequest.optionIdFor(entity));
            }
            if (actions.isEmpty()) {
                throw new ExternalDecisionValidationException(
                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                        "entity selection has no authoritative transition");
            }
            final String action = getController().chooseExternalUiOptions(actions, 1, 1, false, false,
                    "ENTITY_LIST_SELECTION", value -> value).get(0);
            if ("DONE".equals(action)) {
                if (!hasEnoughTargets()) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "entity selection minimum is not satisfied");
                }
                onOk();
                return;
            }
            if ("CANCEL".equals(action)) {
                if (!allowCancel) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.CANCEL_NOT_ALLOWED,
                            "entity selection cannot cancel");
                }
                onCancel();
                return;
            }
            if (action != null && action.startsWith("ENTITY:")) {
                final String optionId = action.substring("ENTITY:".length());
                T selectedEntity = null;
                for (final T candidate : validChoices) {
                    if (ExternalDecisionRequest.optionIdFor(candidate).equals(optionId)) {
                        selectedEntity = candidate;
                        break;
                    }
                }
                if (selectedEntity == null || !selectEntity(selectedEntity)) {
                    throw new ExternalDecisionValidationException(
                            ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                            "entity selection token became stale");
                }
                if (hasAllTargets()) {
                    onOk();
                    return;
                }
                continue;
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.ILLEGAL_OPTION,
                    "unknown entity selection action token");
        }
    }

    @Override
    public final Collection<T> getSelected() {
''')

sync = root / "forge-gui/src/main/java/forge/gamemodes/match/input/InputSyncronizedBase.java"
replace_once(
    sync,
    '''    public void showAndWait() {
        if (getController().hasExternalDecisionProvider()) {
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "legacy GUI input cannot block while the external decision boundary is active");
        }
        getController().getInputQueue().setInput(this);
        awaitLatchRelease();
    }
''',
    '''    public void showAndWait() {
        if (getController().hasExternalDecisionProvider()) {
            if (this instanceof InputSelectEntitiesFromList<?> entitySelection) {
                entitySelection.driveExternal();
                return;
            }
            throw new ExternalDecisionValidationException(
                    ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,
                    "unsupported synchronized input in strict external mode: " + getClass().getSimpleName());
        }
        getController().getInputQueue().setInput(this);
        awaitLatchRelease();
    }
''')

print("WS01_SYNCHRONIZED_INPUT_BRIDGE_APPLIED=TRUE")
