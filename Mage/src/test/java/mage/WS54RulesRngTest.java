package mage;

import mage.cards.Card;
import mage.cards.decks.Deck;
import mage.game.FakeGame;
import mage.game.Game;
import mage.players.Library;
import mage.util.GameRandom;
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
 * WS54 post-repair P-corpus (Mage-module level, no card DB).
 *
 * <p>Supersedes {@code WS54PreRepairM5ReproTest} (pre-repair R1-R5 witness, preserved
 * in git history and {@code WS54_PRE_REPAIR_M5_REPRO.json}). Uses the same proxy-card
 * technique, now asserting the remediated contract through PRODUCTION paths:
 * {@code Deck.getMaindeckCards}, {@code Library.shuffle(Random)}, {@code GameRandom}.</p>
 */
public class WS54RulesRngTest {

    private static final long SEED_A = 0xC0FFEE1234L;
    private static final long SEED_B = 0xDEADBEEFL;
    private static final int DECK_SIZE = 60;
    private static final int FRESH_CONSTRUCTIONS = 25;

    private static final class TrackedLibrary {
        final Library library = new Library(UUID.randomUUID());
        final Map<UUID, String> idToName = new HashMap<>();

        void addTopToBottom(List<String> nameOrderTopFirst, UUID ownerId) {
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

    private static Card stubCard(String name, UUID ownerId) {
        UUID id = UUID.randomUUID();
        return (Card) Proxy.newProxyInstance(
                WS54RulesRngTest.class.getClassLoader(),
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
        // production setup path: PlayerImpl.useDeck -> deck.getMaindeckCards()
        return deck.getMaindeckCards().stream()
                .map(Card::getName)
                .collect(Collectors.toList());
    }

    private static List<String> shuffleNames(List<String> preOrder, GameRandom rng) {
        TrackedLibrary lib = new TrackedLibrary();
        lib.addTopToBottom(preOrder, UUID.randomUUID());
        lib.library.shuffle(rng); // production Fisher-Yates via explicit game-scoped RNG
        return lib.currentNamesTopFirst();
    }

    // P1-setup: same semantic deck input materializes identically across fresh
    // constructions (declared order preserved; multiplicity intact).
    @Test
    public void testP1_SetupMaterializationDeterministic() throws Exception {
        List<String> declared = declaredOrder();
        for (int i = 0; i < FRESH_CONSTRUCTIONS; i++) {
            Deck deck = buildSemanticDeck(UUID.randomUUID());
            List<String> materialized = materializedOrder(deck);
            assertEquals("construction " + i + ": same semantic input must materialize identically",
                    declared, materialized);
        }
    }

    // P1: same setup + same seed, fresh game-scoped RNGs -> same authoritative shuffle.
    @Test
    public void testP1_SameSeedFreshGamesSameShuffle() throws Exception {
        List<String> preOrder = materializedOrder(buildSemanticDeck(UUID.randomUUID()));
        List<String> first = shuffleNames(preOrder, new GameRandom(SEED_A));
        for (int i = 0; i < FRESH_CONSTRUCTIONS; i++) {
            List<String> rerun = shuffleNames(preOrder, new GameRandom(SEED_A));
            assertEquals("fresh RNG " + i + ": same seed + same input must shuffle identically", first, rerun);
        }
        System.out.println("WS54-P1 shuffled head: " + String.join(",", first.subList(0, 6)));
    }

    // P2: fixed pair of different seeds -> demonstrably different controlled output
    // (deterministic control witness, not a statistical test).
    @Test
    public void testP2_DifferentSeedDifferentOutput() throws Exception {
        List<String> preOrder = materializedOrder(buildSemanticDeck(UUID.randomUUID()));
        List<String> outA = shuffleNames(preOrder, new GameRandom(SEED_A));
        List<String> outB = shuffleNames(preOrder, new GameRandom(SEED_B));
        assertNotEquals("P2 control: distinct fixed seeds must yield distinct shuffles", outA, outB);
    }

    // P3: interleaved games -- consumption by B must not alter A vs A-alone.
    @Test
    public void testP3_InterleavedGamesIsolated() {
        GameRandom controlA = new GameRandom(SEED_A);
        int a1 = controlA.nextInt(1_000_000);
        int a2 = controlA.nextInt(1_000_000);
        int a3 = controlA.nextInt(1_000_000);

        GameRandom gameA = new GameRandom(SEED_A);
        GameRandom gameB = new GameRandom(SEED_B);
        assertEquals(a1, gameA.nextInt(1_000_000));
        for (int i = 0; i < 50; i++) {
            gameB.nextInt(1_000_000); // heavy interleaved consumption by another game
        }
        assertEquals(a2, gameA.nextInt(1_000_000));
        for (int i = 0; i < 50; i++) {
            gameB.nextLong();
        }
        assertEquals(a3, gameA.nextInt(1_000_000));
    }

    // P4: AI/UI/non-Rules consumption between two Rules draws must not perturb the game.
    @Test
    public void testP4_NonRulesPerturbationIsolated() {
        GameRandom control = new GameRandom(SEED_A);
        int c1 = control.nextInt(1_000_000);
        int c2 = control.nextInt(1_000_000);

        GameRandom game = new GameRandom(SEED_A);
        assertEquals(c1, game.nextInt(1_000_000));
        // storm of non-Rules consumption on the shared legacy stream (AI search, UI, tests)
        RandomUtil.setSeed(0x12345L);
        for (int i = 0; i < 10_000; i++) {
            RandomUtil.nextInt(1_000_000);
            RandomUtil.nextBoolean();
            RandomUtil.nextDouble();
        }
        assertEquals("P4: non-Rules stream consumption must not perturb the Rules stream",
                c2, game.nextInt(1_000_000));
    }

    // Copy isolation: an AI-simulation copy can never perturb the parent stream.
    @Test
    public void testCopy_DuplicationIsolatesParent() {
        GameRandom parent = new GameRandom(SEED_A);
        int p1 = parent.nextInt(1_000_000);
        GameRandom sim = parent.copy();
        for (int i = 0; i < 100; i++) {
            sim.nextInt(1_000_000); // simulation consumption on the copy
        }
        GameRandom control = new GameRandom(SEED_A);
        control.nextInt(1_000_000);
        assertEquals(p1, new GameRandom(SEED_A).nextInt(1_000_000));
        assertEquals("sim copy consumption must not perturb the parent",
                control.nextInt(1_000_000), parent.nextInt(1_000_000));
    }

    // Game authority: seed identity, explicit flag, copy preservation, fail-closed init.
    @Test
    public void testGame_RulesSeedAuthority() throws Exception {
        Game game = new FakeGame();
        game.setGameOptions(new mage.game.GameOptions()); // FakeGame leaves options null; copy() needs them
        assertNotNull(game.getRulesRandom());
        assertFalse("default construction must be non-credited", game.isRulesSeedExplicit());
        long recordedDefault = game.getRulesSeed();

        game.setRulesSeed(SEED_A);
        assertTrue(game.isRulesSeedExplicit());
        assertEquals(SEED_A, game.getRulesSeed());
        assertEquals(0L, game.getRulesRandomCalls());
        game.getRulesRandom().nextInt(10);
        assertEquals(1L, game.getRulesRandomCalls());

        Game copy = game.copy();
        assertTrue(copy.isRulesSeedExplicit());
        assertEquals(SEED_A, copy.getRulesSeed());
        // copy starts at the parent's current position...
        assertEquals(game.getRulesRandom().nextInt(1_000_000), copy.getRulesRandom().nextInt(1_000_000));
        // ...and consuming the copy does not move the parent
        long before = game.getRulesRandomCalls();
        copy.getRulesRandom().nextInt(1_000_000);
        assertEquals(before, game.getRulesRandomCalls());
    }

    @Test
    public void testGame_CreditedInitFailsClosedWithoutExplicitSeed() throws Exception {
        Game game = new FakeGame();
        game.setRequireExplicitSeed(true);
        java.lang.reflect.Method init = game.getClass().getSuperclass()
                .getDeclaredMethod("init", UUID.class);
        init.setAccessible(true);
        try {
            init.invoke(game, UUID.randomUUID());
            fail("credited init without an explicit seed must fail closed");
        } catch (java.lang.reflect.InvocationTargetException e) {
            assertTrue("expected IllegalStateException, got " + e.getCause(),
                    e.getCause() instanceof IllegalStateException);
        }
        game.setRulesSeed(SEED_A);
        // explicit seed now present: fail-closed gate passes (init may still fail for
        // unrelated empty-game reasons -- only the seed gate is asserted here)
        try {
            init.invoke(game, UUID.randomUUID());
        } catch (java.lang.reflect.InvocationTargetException e) {
            assertFalse("seed gate must pass once explicit; got " + e.getCause(),
                    e.getCause() instanceof IllegalStateException
                            && e.getCause().getMessage().contains("explicit Rules seed"));
        }
    }

    // ---- negative controls: the harness must demonstrably detect divergence ----

    // N-seed: changed seed is detected.
    @Test
    public void testNegative_ChangedSeedDetected() throws Exception {
        List<String> preOrder = materializedOrder(buildSemanticDeck(UUID.randomUUID()));
        List<String> base = shuffleNames(preOrder, new GameRandom(SEED_A));
        List<String> mutated = shuffleNames(preOrder, new GameRandom(SEED_A + 1));
        assertNotEquals("detector must fire on changed seed", base, mutated);
    }

    // N-input: changed setup input is detected.
    @Test
    public void testNegative_ChangedSetupInputDetected() throws Exception {
        List<String> preOrder = materializedOrder(buildSemanticDeck(UUID.randomUUID()));
        List<String> base = shuffleNames(preOrder, new GameRandom(SEED_A));
        List<String> changed = new ArrayList<>(preOrder);
        changed.set(0, changed.get(1).equals("Plains") ? "Island" : "Plains");
        assertNotEquals("detector must fire on changed setup input",
                base, shuffleNames(changed, new GameRandom(SEED_A)));
    }

    // N-outcome: a perturbed recorded outcome is detected by the comparator.
    @Test
    public void testNegative_PerturbedOutcomeDetected() throws Exception {
        List<String> preOrder = materializedOrder(buildSemanticDeck(UUID.randomUUID()));
        List<String> recorded = shuffleNames(preOrder, new GameRandom(SEED_A));
        List<String> tampered = new ArrayList<>(recorded);
        tampered.set(tampered.size() - 1,
                tampered.get(tampered.size() - 1).equals("Plains") ? "Island" : "Plains");
        assertNotEquals("comparator must fire on a perturbed recorded outcome", recorded, tampered);
    }

    // N-mutant: a test-only planted fault (non-game-scoped source) is detected: the
    // mutant's output varies with foreign stream position while the game-scoped
    // control stays fixed.
    @Test
    public void testNegative_NonGameScopedMutantDetected() throws Exception {
        List<String> preOrder = materializedOrder(buildSemanticDeck(UUID.randomUUID()));
        List<String> control = shuffleNames(preOrder, new GameRandom(SEED_A));

        RandomUtil.setSeed(SEED_A);
        List<String> mutantA = shuffleNamesMutant(preOrder);
        // foreign consumption moves the shared stream; the mutant follows it...
        for (int i = 0; i < 13; i++) {
            RandomUtil.nextInt(1_000_000);
        }
        List<String> mutantB = shuffleNamesMutant(preOrder);
        assertNotEquals("planted mutant (global-stream shuffle) must vary with stream position",
                mutantA, mutantB);
        // ...while the game-scoped control is unaffected by the same foreign consumption
        for (int i = 0; i < 13; i++) {
            RandomUtil.nextInt(1_000_000);
        }
        assertEquals("game-scoped control must be immune to foreign consumption",
                control, shuffleNames(preOrder, new GameRandom(SEED_A)));
    }

    /** Test-only planted fault: production Fisher-Yates fed by the shared global stream. */
    private static List<String> shuffleNamesMutant(List<String> preOrder) {
        TrackedLibrary lib = new TrackedLibrary();
        lib.addTopToBottom(preOrder, UUID.randomUUID());
        lib.library.shuffle(); // deprecated non-authoritative path: the planted fault
        return lib.currentNamesTopFirst();
    }

    // P5 support: prints a UUID-agnostic semantic digest for fresh-process comparison.
    @Test
    public void testP5_FreshProcessDigest() throws Exception {
        List<String> preOrder = materializedOrder(buildSemanticDeck(UUID.randomUUID()));
        GameRandom rng = new GameRandom(SEED_A);
        List<String> shuffled = shuffleNames(preOrder, rng);
        String digest = "WS54-P5 seed=" + SEED_A
                + " pre=" + compact(preOrder)
                + " post=" + compact(shuffled)
                + " calls=" + rng.getCallsCount();
        System.out.println(digest);
        assertEquals(DECK_SIZE, shuffled.size());
        assertEquals(DECK_SIZE - 1 + 1, preOrder.size());
    }

    private static String compact(List<String> names) {
        StringBuilder sb = new StringBuilder();
        for (String n : names) {
            sb.append(n.charAt(0));
        }
        return sb.toString();
    }
}
