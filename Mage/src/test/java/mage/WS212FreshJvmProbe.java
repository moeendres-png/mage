package mage;

import mage.cards.Card;
import mage.cards.decks.Deck;
import mage.game.FakeGame;
import mage.game.Game;
import mage.players.Library;

import java.lang.reflect.Field;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/**
 * WS212 fresh-JVM probe (engine-only, no Commander-Lab pilot logic).
 *
 * <p>Drives the exact production initial-shuffle path behind
 * {@code PlayerImpl.shuffleLibrary}:
 * {@code Deck.getMaindeckCards} (declared-order materialization) -&gt;
 * {@code Library.addAll} (the {@code useDeck} path) -&gt;
 * {@code Library.shuffle(game.getRulesRandom())} (the Rules-stream shuffle),
 * after an explicit {@code setRulesSeed} on a real {@link FakeGame}.</p>
 *
 * <p>Prints one UUID-agnostic digest line ({@code WS212-PROBE ...}) binding
 * pre-start deck order, explicit seed, post-shuffle order, opening hand
 * (top 7 of the shuffled library) and the Rules-consumption count. The JUnit
 * twin ({@link WS212RulesSeedAuthorityTest}) launches this class in two
 * separate JVM processes and requires byte-identical digests for the same
 * seed, and a demonstrably different digest for a different seed.</p>
 */
public final class WS212FreshJvmProbe {

    private WS212FreshJvmProbe() {
    }

    public static void main(String[] args) throws Exception {
        long seed = Long.parseLong(args[0]);
        UUID ownerId = UUID.randomUUID();

        Deck deck = buildSemanticDeck(ownerId);
        List<String> preOrder = materializedNames(deck);

        Game game = new FakeGame();
        game.setRulesSeed(seed);
        game.setRequireExplicitSeed(true);

        Map<UUID, String> idToName = new HashMap<>();
        for (Card card : deck.getMaindeckCards()) {
            idToName.put(card.getId(), card.getName());
        }
        Library library = new Library(ownerId);
        // Exact path PlayerImpl.useDeck takes into the library (insertion only, no RNG).
        library.addAll(deck.getMaindeckCards(), game);
        // Exact RNG call inside PlayerImpl.shuffleLibrary (event plumbing excluded;
        // the bare game carries no abilities, and the full-game twin covers events).
        library.shuffle(game.getRulesRandom());

        List<UUID> ids = library.getCardList();
        List<String> postOrder = new ArrayList<>(ids.size());
        for (UUID id : ids) {
            postOrder.add(idToName.get(id));
        }
        List<String> openingHand = postOrder.subList(0, 7);

        System.out.println("WS212-PROBE"
                + " seed=" + game.getRulesSeed()
                + " explicit=" + game.isRulesSeedExplicit()
                + " pre=" + String.join(",", preOrder)
                + " post=" + String.join(",", postOrder)
                + " hand=" + String.join(",", openingHand)
                + " calls=" + game.getRulesRandomCalls());
    }

    private static Deck buildSemanticDeck(UUID ownerId) throws Exception {
        Deck deck = new Deck();
        Field cardsField = Deck.class.getDeclaredField("cards");
        cardsField.setAccessible(true);
        @SuppressWarnings("unchecked")
        Set<Card> cards = (Set<Card>) cardsField.get(deck);
        for (int i = 0; i < 60; i++) {
            String name = i < 20 ? "Plains" : (i < 40 ? "Island" : "Forest");
            cards.add(stubCard(name, ownerId));
        }
        return deck;
    }

    private static List<String> materializedNames(Deck deck) {
        List<String> names = new ArrayList<>();
        for (Card card : deck.getMaindeckCards()) {
            names.add(card.getName());
        }
        return names;
    }

    private static Card stubCard(String name, UUID ownerId) {
        UUID id = UUID.randomUUID();
        return (Card) java.lang.reflect.Proxy.newProxyInstance(
                WS212FreshJvmProbe.class.getClassLoader(),
                new Class<?>[]{Card.class},
                (proxy, method, methodArgs) -> {
                    switch (method.getName()) {
                        case "getId":
                            return id;
                        case "getName":
                            return name;
                        case "isExtraDeckCard":
                            return false;
                        case "isOwnedBy":
                            return true;
                        case "getOwnerId":
                            return ownerId;
                        case "setZone":
                            return null;
                        case "toString":
                            return name + "{" + id + "}";
                        case "hashCode":
                            return System.identityHashCode(proxy);
                        case "equals":
                            return proxy == methodArgs[0];
                        default:
                            Class<?> ret = method.getReturnType();
                            if (ret == boolean.class) {
                                return false;
                            }
                            if (ret == int.class) {
                                return 0;
                            }
                            return null;
                    }
                });
    }
}
