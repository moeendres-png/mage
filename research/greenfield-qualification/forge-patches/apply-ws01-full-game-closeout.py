#!/usr/bin/env python3
from pathlib import Path
import sys

if len(sys.argv) != 2:
    raise SystemExit("usage: apply-ws01-full-game-closeout.py <forge-root>")

root = Path(sys.argv[1]).resolve()
path = root / "forge-gui-desktop/src/test/java/forge/net/ExternalDecisionFullGameRunner.java"
text = path.read_text(encoding="utf-8")


def replace_once(old: str, new: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one full-game runner anchor, found {count}: {old[:120]!r}")
    text = text.replace(old, new, 1)


replace_once(
    "import forge.game.player.Player;\n",
    "import forge.deck.Deck;\n"
    "import forge.deck.DeckSection;\n"
    "import forge.game.player.Player;\n"
    "import forge.item.PaperCard;\n"
    "import forge.model.FModel;\n"
)

replace_once(
    "                case \"STARTING_HAND\" -> selected.add(lowestOptionId(request));\n"
    "                default -> throw new ExternalDecisionValidationException(\n",
    "                case \"STARTING_HAND\" -> selected.add(lowestOptionId(request));\n"
    "                case \"MAX_HAND_SIZE_DISCARD\" -> selectLowestExact(request, selected);\n"
    "                default -> throw new ExternalDecisionValidationException(\n"
)

replace_once(
    "        private static String lowestOptionId(final ExternalDecisionRequest request) {\n"
    "            String best = null;\n"
    "            for (final ExternalDecisionRequest.Option option : request.getOptions()) {\n"
    "                if (best == null || option.getOptionId().compareTo(best) < 0) {\n"
    "                    best = option.getOptionId();\n"
    "                }\n"
    "            }\n"
    "            if (best == null) {\n"
    "                throw new ExternalDecisionValidationException(\n"
    "                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION,\n"
    "                        \"authoritative option set is empty for \" + request.getDecisionKind());\n"
    "            }\n"
    "            return best;\n"
    "        }\n"
    "    }\n\n"
    "    public static void main(final String[] args) throws Exception {\n",
    "        private static String lowestOptionId(final ExternalDecisionRequest request) {\n"
    "            String best = null;\n"
    "            for (final ExternalDecisionRequest.Option option : request.getOptions()) {\n"
    "                if (best == null || option.getOptionId().compareTo(best) < 0) {\n"
    "                    best = option.getOptionId();\n"
    "                }\n"
    "            }\n"
    "            if (best == null) {\n"
    "                throw new ExternalDecisionValidationException(\n"
    "                        ExternalDecisionValidationException.Code.ILLEGAL_OPTION,\n"
    "                        \"authoritative option set is empty for \" + request.getDecisionKind());\n"
    "            }\n"
    "            return best;\n"
    "        }\n\n"
    "        private static void selectLowestExact(final ExternalDecisionRequest request, final List<String> selected) {\n"
    "            final List<ExternalDecisionRequest.Option> ordered = new ArrayList<>(request.getOptions());\n"
    "            ordered.sort(java.util.Comparator.comparing(ExternalDecisionRequest.Option::getOptionId));\n"
    "            final int count = request.getMinimumSelection();\n"
    "            if (count < 0 || count > ordered.size() || count != request.getMaximumSelection()) {\n"
    "                throw new ExternalDecisionValidationException(\n"
    "                        ExternalDecisionValidationException.Code.UNSUPPORTED_DECISION_PATH,\n"
    "                        \"qualification policy requires exact cardinality for \" + request.getDecisionKind());\n"
    "            }\n"
    "            for (int i = 0; i < count; i++) {\n"
    "                selected.add(ordered.get(i).getOptionId());\n"
    "            }\n"
    "        }\n"
    "    }\n\n"
    "    private static List<Deck> createQualificationDecks() {\n"
    "        final List<Deck> decks = new ArrayList<>();\n"
    "        final PaperCard commander = FModel.getMagicDb().getCommonCards().getCard(\"Isamaru, Hound of Konda\");\n"
    "        if (commander == null) {\n"
    "            throw new IllegalStateException(\"qualification commander card is unavailable\");\n"
    "        }\n"
    "        for (int i = 0; i < 4; i++) {\n"
    "            final Deck deck = TestDeckLoader.createMinimalDeck(\"Plains\", 12);\n"
    "            deck.getOrCreate(DeckSection.Commander).add(commander);\n"
    "            decks.add(deck);\n"
    "        }\n"
    "        return decks;\n"
    "    }\n\n"
    "    public static void main(final String[] args) throws Exception {\n"
)

replace_once(
    "                    .useAiForRemotePlayers(false)\n"
    "                    .commander(true)\n"
    "                    .gameTimeout(300000)\n",
    "                    .useAiForRemotePlayers(false)\n"
    "                    .commander(true)\n"
    "                    .decks(createQualificationDecks())\n"
    "                    .gameTimeout(120000)\n"
)

path.write_text(text, encoding="utf-8")
print("WS01_FULL_GAME_CLOSEOUT_APPLIED=TRUE")
