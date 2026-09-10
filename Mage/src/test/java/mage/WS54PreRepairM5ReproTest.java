package mage;

import mage.cards.Card;
import mage.cards.decks.Deck;
import mage.game.Game;
import mage.players.Library;
import mage.util.RandomUtil;
import org.junit.Test;

import java.lang.reflect.Field;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

import static org.junit.Assert.*;

/**
 * WS54 FIRST GATE -- pre-repair reproduction of the WS52 M5 failure at the exact
 * source-lock pin (0c1f455e...).
 *
 * <p>Exercises PRODUCTION code paths only (no test-helper forks):
 * <ul>
 *   <li>{@code Deck.getMaindeckCards()} -- production setup materialization;</li>
 *   <li>{@code Library.putOnTop / shuffle / getCardList} -- production library + shuffle;</li>
 *   <li>{@code RandomUtil} -- production global RNG.</li>
 * </ul>
 * Card objects are dynamic-proxy stubs carrying a fresh random UUID each, exactly
 * like production {@code CardInfo.createCard()} assigns a fresh UUID per created card.
 * No card database is required.</p>
 *
 * <p>This file is a PRE-REPAIR witness. Post-repair P1-P6 tests supersede it; the
 * R5 topology assertion in particular must be revisited once a game-scoped RNG exists.</p>
 */
public class WS54PreRepairM5ReproTest {

    private static final long SEED = 0xC0FFEE1234L;
    private static final int DECK_SIZE = 60;

    /** A tracked library: production Library plus the uuid-&gt;name map of its content. */
    private static final class TrackedLibrary {
        final Library library = new Library(UUID.randomUUID());
        final Map<UUID, String> idToName = new HashMap<>();

        void addTopToBottom(List<String> nameOrderTopFirst, UUID ownerId) {
            // putOnTop adds first, so insert reversed to keep top-to-bottom == nameOrder
            for (int i = nameOrderTopFirst.size() - 1; i >= 0; i--) {
                Card card = stubCard(nameOrderTopFirst.get(i), ownerId);
                library.putOnTop(card, (Game) null);
                idToName.put(card.getId(), card.getName());
            }
        }

        List<String> currentNamesTopFirst() {
            List<String> names = new ArrayList<>();
            for (UUID id : library.getCardList()) {
                names.add(idToName.get(id));
            }
            return names;
        }
    }

    /**
     * Builds a production {@link Deck} whose declared (insertion) order is fixed and
     * semantically stable: 20 Plains, 20 Island, 20 Forest -- each card a fresh
     * random-UUID instance as in production deck load.
     */
    private static Deck buildSemanticDeck(UUID ownerId) throws Exception {
        Deck deck = new Deck();
        Field cardsField = Deck.class.getDeclaredField("cards");
        cardsField.setAccessible(true);
        @SuppressWarnings("unchecked")
        Set<Card> cards = (Set<Card>) cardsField.get(deck);
        for (String name : declaredOrder()) {
            cards.add(stubCard(name, ownerId));
        }
        return deck;
    }

    /**
     * Dynamic-proxy {@link Card} stub. Only production-touched methods are stubbed:
     * getId/getName/isExtraDeckCard (setup filter), isOwnedBy/setZone/getOwnerId
     * (library load). Identity semantics preserved for equals/hashCode.
     */
    private static Card stubCard(String name, UUID ownerId) {
        UUID id = UUID.randomUUID();
        return (Card) Proxy.newProxyInstance(
                WS54PreRepairM5ReproTest.class.getClassLoader(),
                new Class<?>[]{Card.class},
                (proxy, method, args) -> {
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
                            return proxy == args[0];
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

    private static List<String> declaredOrder() {
        List<String> order = new ArrayList<>(DECK_SIZE);
        for (int i = 0; i < DECK_SIZE; i++) {
            order.add(i < 20 ? "Plains" : (i < 40 ? "Island" : "Forest"));
        }
        return order;
    }

    private static List<String> materializedOrder(Deck deck) {
        // EXACT production setup path: PlayerImpl.useDeck -> deck.getMaindeckCards()
        return deck.getMaindeckCards().stream()
                .map(Card::getName)
                .collect(Collectors.toList());
    }

    // R3: unordered input collection materialization destroys the declared order.
    @Test
    public void testR3_UnorderedMaterializationDestroysDeclaredOrder() throws Exception {
        UUID ownerId = UUID.randomUUID();
        Deck deck = buildSemanticDeck(ownerId);

        List<String> declared = declaredOrder();
        List<String> materialized = materializedOrder(deck);

        System.out.println("WS54-R3 declared    : " + String.join(",", declared.subList(0, 8)) + "...");
        System.out.println("WS54-R3 materialized: " + String.join(",", materialized.subList(0, 8)) + "...");

        assertEquals(DECK_SIZE, materialized.size());
        // same multiset (multiplicity preserved), order NOT preserved
        assertEquals(
                declared.stream().sorted().collect(Collectors.toList()),
                materialized.stream().sorted().collect(Collectors.toList()));
        assertNotEquals("pre-repair expectation: HashSet materialization must scramble "
                + "the declared deck order; if this fails the defect may already be fixed", declared, materialized);
    }

    // R1: identical explicit seed + semantically identical deck/setup input can produce
    // different initial shuffled state across fresh runs (two fresh deck constructions).
    @Test
    public void testR1_SameSeedSameSemanticDeckDivergesAcrossFreshConstructions() throws Exception {
        Deck deckA = buildSemanticDeck(UUID.randomUUID());
        Deck deckB = buildSemanticDeck(UUID.randomUUID());

        List<String> preA = materializedOrder(deckA);
        List<String> preB = materializedOrder(deckB);
        System.out.println("WS54-R1 pre-shuffle A: " + String.join(",", preA.subList(0, 6)) + "...");
        System.out.println("WS54-R1 pre-shuffle B: " + String.join(",", preB.subList(0, 6)) + "...");
        assertNotEquals("pre-repair expectation: two fresh constructions of the same semantic "
                + "deck must yield different pre-shuffle sequences", preA, preB);

        TrackedLibrary libA = new TrackedLibrary();
        libA.addTopToBottom(preA, UUID.randomUUID());
        TrackedLibrary libB = new TrackedLibrary();
        libB.addTopToBottom(preB, UUID.randomUUID());

        RandomUtil.setSeed(SEED);
        libA.library.shuffle();
        List<String> shuffledA = libA.currentNamesTopFirst();

        RandomUtil.setSeed(SEED);
        libB.library.shuffle();
        List<String> shuffledB = libB.currentNamesTopFirst();

        System.out.println("WS54-R1 shuffled A: " + String.join(",", shuffledA.subList(0, 6)) + "...");
        System.out.println("WS54-R1 shuffled B: " + String.join(",", shuffledB.subList(0, 6)) + "...");

        assertNotEquals("R1 REPRODUCED: same seed + semantically identical deck input produced "
                + "different initial shuffled state", shuffledA, shuffledB);
    }

    // R2: divergence originates at/before the first shuffle input, not from later decisions.
    // Control: same seed + IDENTICAL input order -> identical shuffle (RNG is seed-deterministic).
    // Experiment: same seed + PERMUTED input order -> different shuffle.
    @Test
    public void testR2_DivergenceOriginatesAtFirstShuffleInput() {
        List<String> input = declaredOrder();

        RandomUtil.setSeed(SEED);
        TrackedLibrary control1 = new TrackedLibrary();
        control1.addTopToBottom(input, UUID.randomUUID());
        control1.library.shuffle();

        RandomUtil.setSeed(SEED);
        TrackedLibrary control2 = new TrackedLibrary();
        control2.addTopToBottom(input, UUID.randomUUID());
        control2.library.shuffle();

        assertEquals("control: identical seed + identical input must shuffle identically "
                        + "(else the RNG itself is broken, not the input pipeline)",
                control1.currentNamesTopFirst(), control2.currentNamesTopFirst());

        List<String> permuted = new ArrayList<>(input);
        java.util.Collections.reverse(permuted);

        RandomUtil.setSeed(SEED);
        TrackedLibrary experiment = new TrackedLibrary();
        experiment.addTopToBottom(permuted, UUID.randomUUID());
        experiment.library.shuffle();

        assertNotEquals("R2 REPRODUCED: same seed but different pre-shuffle input order "
                        + "yields a different shuffle -- divergence enters at/before the first "
                        + "shuffle, independent of any later game decision",
                control1.currentNamesTopFirst(), experiment.currentNamesTopFirst());
    }

    // R4: a global/shared random stream lets another consumer perturb a game's later
    // Rules-random result.
    @Test
    public void testR4_SharedStreamAllowsCrossConsumerPerturbation() {
        final int bound = 1_000_000;

        // control: game A draws twice in isolation
        RandomUtil.setSeed(SEED);
        int a1 = RandomUtil.nextInt(bound);
        int a2Control = RandomUtil.nextInt(bound);

        // experiment: same seed, same first draw, then a FOREIGN consumer (other game / AI)
        // consumes from the same shared stream before game A's second draw
        RandomUtil.setSeed(SEED);
        int a1Again = RandomUtil.nextInt(bound);
        assertEquals(a1, a1Again);
        for (int i = 0; i < 7; i++) {
            RandomUtil.nextInt(bound); // foreign consumption: AI search, other game, UI
        }
        int a2Perturbed = RandomUtil.nextInt(bound);

        System.out.println("WS54-R4 control=" + a2Control + " perturbed=" + a2Perturbed);
        assertNotEquals("R4 REPRODUCED: foreign consumption of the shared global stream "
                + "changed game A's later draw", a2Control, a2Perturbed);

        // topology proof: one single static Random instance is shared JVM-wide
        assertSame("R4 topology: RandomUtil exposes a single JVM-global Random",
                RandomUtil.getRandom(), RandomUtil.getRandom());
    }

    // R5: at least one production-reachable Rules shuffle path cannot consume an
    // explicitly game-scoped controlled RNG (none exists at this pin).
    @Test
    public void testR5_ProductionShuffleBypassesGameScopedRng() throws Exception {
        // Library.shuffle() -- the production Fisher-Yates used by every library shuffle --
        // takes NO game/RNG parameter: it can only draw from the JVM-global stream.
        assertEquals("pre-repair expectation: Library.shuffle() takes no game/RNG argument, "
                        + "so no production library shuffle can be game-scoped",
                0, Library.class.getMethod("shuffle").getParameterCount());
    }
}
