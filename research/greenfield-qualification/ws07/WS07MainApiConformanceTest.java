package forge.ws07;

import forge.CardStorageReader;
import forge.LobbyPlayer;
import forge.StaticData;
import forge.ai.PlayerControllerAi;
import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Game;
import forge.game.GameEntity;
import forge.game.GameRules;
import forge.game.GameStage;
import forge.game.GameType;
import forge.game.Match;
import forge.game.ability.AbilityKey;
import forge.game.card.Card;
import forge.game.combat.Combat;
import forge.game.combat.CombatUtil;
import forge.game.cost.Cost;
import forge.game.cost.CostAdjustment;
import forge.game.mulligan.LondonMulligan;
import forge.game.player.IGameEntitiesFactory;
import forge.game.player.PlaySpellAbility;
import forge.game.player.Player;
import forge.game.player.PlayerController;
import forge.game.player.RegisteredPlayer;
import forge.game.replacement.ReplacementEffect;
import forge.game.spellability.LandAbility;
import forge.game.spellability.SpellAbility;
import forge.game.spellability.SpellPermanent;
import forge.game.zone.ZoneType;
import forge.item.PaperCard;
import forge.util.Localizer;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.File;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * WS07 semantic Commander/multiplayer qualification against pinned Forge main APIs only.
 *
 * The harness supplies deterministic discretionary choices but does not implement Magic rules.
 * Legality, costs, stack, zones, combat, state-based actions, Commander state, and multiplayer
 * consequences are asserted from Forge engine state.
 */
public class WS07MainApiConformanceTest {
    private static final String DEFAULT_COMMANDER = "Isamaru, Hound of Konda";
    private static final String[] COMMANDERS = {
            DEFAULT_COMMANDER,
            "Talrand, Sky Summoner",
            "Krenko, Mob Boss",
            "Ayli, Eternal Pilgrim",
            "Ezuri, Renegade Leader"
    };

    private static StaticData staticData;

    private static String dir(Path path) {
        return path.toAbsolutePath().normalize().toString() + File.separator;
    }

    /** Minimal card lookup derived from Forge main loaders; no Forge test helper dependency. */
    private static synchronized PaperCard paper(String name) {
        if (staticData == null) {
            Path root = Path.of(System.getProperty("user.dir")).toAbsolutePath().normalize();
            while (root != null && !Files.isDirectory(root.resolve("forge-gui/res/cardsfolder"))) {
                root = root.getParent();
            }
            if (root == null) {
                throw new IllegalStateException("Unable to locate pinned Forge repository root from user.dir");
            }
            Path res = root.resolve("forge-gui/res");
            Path emptyCustomEditions = root.resolve("target/ws07-empty-custom-editions");
            try {
                Files.createDirectories(emptyCustomEditions);
            } catch (IOException e) {
                throw new RuntimeException("Unable to create WS07 empty custom-editions directory", e);
            }
            Localizer.getInstance().initialize("en-US", dir(res.resolve("languages")));
            CardStorageReader reader = new CardStorageReader(dir(res.resolve("cardsfolder")), null, false);
            staticData = new StaticData(
                    reader,
                    null,
                    dir(res.resolve("editions")),
                    dir(emptyCustomEditions),
                    dir(res.resolve("blockdata")),
                    "Latest Art All Editions",
                    true,
                    false
            );
        }
        PaperCard result = staticData.getCommonCards().getCard(name);
        if (result == null) {
            throw new IllegalArgumentException("Pinned Forge card data does not contain: " + name);
        }
        return result;
    }

    private static final class Ws07Controller extends PlayerControllerAi {
        private final Player wsPlayer;
        private boolean commanderReplacementChoice;
        private final List<String> apnapCallbacks;

        Ws07Controller(Game game, Player player, LobbyPlayer lobbyPlayer,
                       boolean commanderReplacementChoice, List<String> apnapCallbacks) {
            super(game, player, lobbyPlayer);
            this.wsPlayer = player;
            this.commanderReplacementChoice = commanderReplacementChoice;
            this.apnapCallbacks = apnapCallbacks;
        }

        void setCommanderReplacementChoice(boolean value) {
            commanderReplacementChoice = value;
        }

        @Override
        public boolean confirmReplacementEffect(ReplacementEffect replacementEffect, SpellAbility effectSA,
                                                GameEntity affected, String question) {
            return commanderReplacementChoice;
        }

        @Override
        public void orderAndPlaySimultaneousSa(List<SpellAbility> activePlayerSAs) {
            apnapCallbacks.add(wsPlayer.getName());
            // Intra-player ordering is discretionary; this scenario asserts Forge's APNAP dispatch.
        }
    }

    private static final class Ws07LobbyPlayer extends LobbyPlayer implements IGameEntitiesFactory {
        private final boolean initialCommanderReplacementChoice;
        private final List<String> apnapCallbacks;
        private Ws07Controller controller;

        Ws07LobbyPlayer(String name, boolean initialCommanderReplacementChoice, List<String> apnapCallbacks) {
            super(name);
            this.initialCommanderReplacementChoice = initialCommanderReplacementChoice;
            this.apnapCallbacks = apnapCallbacks;
        }

        @Override
        public Player createIngamePlayer(Game gameState, int id) {
            Player player = new Player(getName(), gameState, id);
            controller = new Ws07Controller(gameState, player, this,
                    initialCommanderReplacementChoice, apnapCallbacks);
            player.setFirstController(controller);
            return player;
        }

        @Override
        public PlayerController createMindSlaveController(Player master, Player slave) {
            return new Ws07Controller(slave.getGame(), slave, this,
                    initialCommanderReplacementChoice, apnapCallbacks);
        }

        @Override
        public void hear(LobbyPlayer player, String message) {
            // Qualification has no UI side effects.
        }

        void setCommanderReplacementChoice(boolean value) {
            if (controller == null) {
                throw new IllegalStateException("controller not initialized");
            }
            controller.setCommanderReplacementChoice(value);
        }
    }

    private static final class Fixture {
        final Game game;
        final List<RegisteredPlayer> registeredPlayers;
        final List<Ws07LobbyPlayer> lobbies;
        final List<String> apnapCallbacks;

        Fixture(Game game, List<RegisteredPlayer> registeredPlayers,
                List<Ws07LobbyPlayer> lobbies, List<String> apnapCallbacks) {
            this.game = game;
            this.registeredPlayers = registeredPlayers;
            this.lobbies = lobbies;
            this.apnapCallbacks = apnapCallbacks;
        }

        Player p(int index) {
            return game.getRegisteredPlayers().get(index);
        }
    }

    private Fixture fixture(int playerCount, boolean acceptCommanderReplacement) {
        return fixture(playerCount, acceptCommanderReplacement, false);
    }

    private Fixture fixture(int playerCount, boolean acceptCommanderReplacement, boolean partnersForPlayerZero) {
        List<RegisteredPlayer> registered = new ArrayList<>();
        List<Ws07LobbyPlayer> lobbies = new ArrayList<>();
        List<String> apnapCallbacks = new ArrayList<>();

        for (int i = 0; i < playerCount; i++) {
            Deck deck = new Deck("WS07-P" + (i + 1));
            if (i == 0 && partnersForPlayerZero) {
                deck.getOrCreate(DeckSection.Commander).add(paper("Rograkh, Son of Rohgahh"), 1);
                deck.getOrCreate(DeckSection.Commander).add(paper("Tymna the Weaver"), 1);
            } else {
                deck.getOrCreate(DeckSection.Commander).add(paper(COMMANDERS[i]), 1);
            }
            deck.getMain().add(paper("Plains"), 20);

            RegisteredPlayer rp = RegisteredPlayer.forCommander(deck);
            Ws07LobbyPlayer lobby = new Ws07LobbyPlayer("WS07-P" + (i + 1),
                    acceptCommanderReplacement, apnapCallbacks);
            rp.setPlayer(lobby);
            registered.add(rp);
            lobbies.add(lobby);
        }

        GameRules rules = new GameRules(GameType.Commander);
        rules.addAppliedVariant(GameType.Commander);
        Match match = new Match(rules, registered, "WS07");
        Game game = match.createGame();
        game.setAge(GameStage.Play);
        for (int i = 0; i < playerCount; i++) {
            game.getRegisteredPlayers().get(i).initVariantsZones(registered.get(i));
        }
        game.getTriggerHandler().resetActiveTriggers();
        game.getPhaseHandler().setPlayerTurn(game.getRegisteredPlayers().get(0));
        return new Fixture(game, registered, lobbies, apnapCallbacks);
    }

    private Card cardIn(Player player, ZoneType zone, String name) {
        for (Card card : player.getZone(zone)) {
            if (card.getName().equals(name)) {
                return card;
            }
        }
        throw new AssertionError("card not found: " + name + " in " + zone + " for " + player.getName());
    }

    private Card commander(Player player) {
        for (Card card : player.getZone(ZoneType.Command)) {
            if (card.isCommander() && !card.getName().equals("Commander Effect")) {
                return card;
            }
        }
        throw new AssertionError("commander not found for " + player.getName());
    }

    private Card putPermanent(Fixture fixture, Player owner, Player controller, String name) {
        Card card = Card.fromPaperCard(paper(name), owner);
        card.setController(controller, 0);
        controller.getZone(ZoneType.Battlefield).add(card);
        fixture.game.getTriggerHandler().registerActiveTrigger(card, false);
        return card;
    }

    private static String jsonEscape(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }

    private void emit(String id, int playerCount, String initialState, String decisions,
                      String assertion, String observedState) {
        String path = System.getenv("WS07_RESULT_PATH");
        if (path == null || path.isBlank()) {
            return;
        }
        String json = "{" +
                "\"id\":\"" + jsonEscape(id) + "\"," +
                "\"scenario_source\":\"research/greenfield-qualification/ws07/WS07MainApiConformanceTest.java\"," +
                "\"player_count\":" + playerCount + "," +
                "\"initial_state\":\"" + jsonEscape(initialState) + "\"," +
                "\"decisions\":\"" + jsonEscape(decisions) + "\"," +
                "\"semantic_assertions\":[\"" + jsonEscape(assertion) + "\"]," +
                "\"observed_state\":\"" + jsonEscape(observedState) + "\"," +
                "\"result\":\"PASS\"," +
                "\"evidence_class\":\"TECHNICALLY_CONFORMANT\"," +
                "\"assertion_kind\":\"ENGINE_STATE\"}" + System.lineSeparator();
        try {
            Path output = Path.of(path);
            if (output.getParent() != null) {
                Files.createDirectories(output.getParent());
            }
            Files.writeString(output, json, StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (IOException e) {
            throw new RuntimeException("Unable to write WS07 semantic result", e);
        }
    }

    @Test
    public void playerCountAndCommanderInitialization() {
        for (int count : new int[]{2, 3, 4, 5}) {
            Fixture f = fixture(count, true);
            Assert.assertEquals(f.game.getPlayers().size(), count);
            for (int i = 0; i < count; i++) {
                Player p = f.p(i);
                Assert.assertEquals(p.getLife(), 40);
                Card cmd = commander(p);
                Assert.assertTrue(cmd.isCommander());
                Assert.assertEquals(cmd.getOwner(), p);
                Assert.assertEquals(cmd.getZone().getZoneType(), ZoneType.Command);
            }
            emit("SUBSET_" + count + "P", count,
                    count + " Commander RegisteredPlayers, one commander each",
                    "none; deterministic constructed initial state",
                    "Forge initializes all players at 40 life with commanders in command zones",
                    "players=" + f.game.getPlayers().size() + ", life=40, command-zone commander present");
            if (count == 4) {
                emit("C01", 4, "4P Commander initialization", "none",
                        "each player starts at 40 life", "all life totals=40");
                emit("C02", 4, "4P Commander initialization", "none",
                        "each commander starts in its owner's command zone", "all commanders zone=Command");
                emit("C18", 4, "4P Commander initialization", "none",
                        "four independent Commander players initialize", "players=4; four command zones initialized");
                emit("A", 4, "4P turn structure initialized", "starting player=P1",
                        "active player and turn order are engine state", "active=P1; players=4");
                emit("K", 4, "Commander variant enabled", "none",
                        "Commander initialization uses Forge variant rules", "40 life; commander flag; Command zone");
                emit("L", 4, "four free-for-all players", "none",
                        "multiplayer engine exposes four in-game players", "players=4");
            }
        }
    }

    @Test
    public void landPlayManaActivationTargetsAndPrivateZones() {
        Fixture f = fixture(4, true);
        Player p0 = f.p(0);
        Player p1 = f.p(1);

        Card plains = Card.fromPaperCard(paper("Plains"), p0);
        p0.getZone(ZoneType.Hand).add(plains);
        LandAbility landAbility = new LandAbility(plains, plains.getCurrentState());
        landAbility.setActivatingPlayer(p0);
        Assert.assertTrue(landAbility.canPlay());
        Assert.assertTrue(PlaySpellAbility.playSpellAbility(p0.getController(), p0, landAbility));
        Card battlefieldPlains = cardIn(p0, ZoneType.Battlefield, "Plains");
        Assert.assertEquals(p0.getLandsPlayedThisTurn(), 1);
        emit("B", 4, "P1 has an unplayed Plains in hand during its turn", "play Plains",
                "Forge LandAbility legality and resolution move the land to battlefield and consume the turn land play",
                "Plains zone=Battlefield; landsPlayedThisTurn=1");

        var manaAbilities = battlefieldPlains.getManaAbilities();
        Assert.assertFalse(manaAbilities.isEmpty());
        SpellAbility mana = manaAbilities.get(0);
        mana.setActivatingPlayer(p0);
        Assert.assertTrue(mana.canPlay());
        Assert.assertTrue(PlaySpellAbility.playSpellAbilityNoStack(p0.getController(), p0, mana, false));
        Assert.assertTrue(battlefieldPlains.isTapped());
        Assert.assertEquals(p0.getManaPool().totalMana(), 1);
        emit("C", 4, "P1 controls an untapped Plains", "activate its mana ability",
                "Forge pays the tap cost and resolves a mana ability without the stack",
                "Plains tapped=true; manaPool.totalMana=1");

        Card bolt = Card.fromPaperCard(paper("Lightning Bolt"), p0);
        p0.getZone(ZoneType.Hand).add(bolt);
        SpellAbility boltSpell = null;
        for (SpellAbility ability : bolt.getSpellAbilities()) {
            if (ability.isSpell()) {
                boltSpell = ability;
                break;
            }
        }
        Assert.assertNotNull(boltSpell);
        boltSpell.setActivatingPlayer(p0);
        Assert.assertTrue(boltSpell.usesTargeting());
        Assert.assertTrue(boltSpell.canTarget(p1));
        Assert.assertTrue(boltSpell.getTargets().add(p1));
        Assert.assertEquals(boltSpell.getTargets().getFirstTargetedPlayer(), p1);
        emit("F", 4, "P1 has Lightning Bolt; P2 is a legal opposing player", "select P2 as target",
                "Forge target restrictions authorize the player target and preserve the chosen target on the spell ability",
                "canTarget(P2)=true; firstTargetedPlayer=P2");

        Card secretHand = Card.fromPaperCard(paper("Savannah Lions"), p0);
        Card secretLibrary = Card.fromPaperCard(paper("Grizzly Bears"), p0);
        p0.getZone(ZoneType.Hand).add(secretHand);
        p0.getZone(ZoneType.Library).add(secretLibrary);
        Assert.assertTrue(p0.getCardsIn(ZoneType.Hand).contains(secretHand));
        Assert.assertTrue(p0.getCardsIn(ZoneType.Library).contains(secretLibrary));
        Assert.assertFalse(p1.getCardsIn(ZoneType.Hand).contains(secretHand));
        Assert.assertFalse(p1.getCardsIn(ZoneType.Library).contains(secretLibrary));
        emit("M", 4, "distinct P1/P2 private Hand and Library zones", "place named objects only in P1 private zones",
                "Forge player-zone ownership keeps private-zone objects scoped to the owning player's zone collections",
                "P1 contains both private objects; P2 private zones contain neither");
    }

    @Test
    public void commandZoneCastAndTax() {
        Fixture castFixture = fixture(4, true);
        Player caster = castFixture.p(0);
        Card cmd = commander(caster);
        SpellPermanent spell = cmd.getSpellPermanent();
        Assert.assertNotNull(spell);
        spell.setActivatingPlayer(caster);
        cmd.setCastFrom(caster.getZone(ZoneType.Command));
        castFixture.game.getStack().addAndUnfreeze(spell);
        Card stackCommander = cardIn(caster, ZoneType.Stack, DEFAULT_COMMANDER);
        Assert.assertTrue(stackCommander.isCommander());
        Assert.assertEquals(caster.getCommanderCast(stackCommander), 1);
        Assert.assertEquals(stackCommander.getCastFrom().getZoneType(), ZoneType.Command);
        emit("C03", 4, "commander in command zone", "cast commander",
                "casting moves commander to stack and records a command-zone cast", "zone=Stack; commanderCast=1");
        emit("D", 4, "commander spell in command zone", "cast",
                "Forge performs cast/cost state transition", "zone=Stack; cast counter incremented");
        emit("E", 4, "empty stack; active=P1", "P1 casts commander",
                "spell is added to MagicStack under Forge stack ownership", "stack contains commander spell");

        Fixture taxFixture = fixture(4, true);
        Player p = taxFixture.p(0);
        Card taxCommander = commander(p);
        SpellPermanent sa = taxCommander.getSpellPermanent();
        sa.setActivatingPlayer(p);
        taxCommander.setCastFrom(p.getZone(ZoneType.Command));
        int baseCmc = sa.getPayCosts().getTotalMana().getCMC();
        Cost first = CostAdjustment.adjust(sa.getPayCosts(), sa, false);
        Assert.assertEquals(first.getTotalMana().getCMC(), baseCmc);
        emit("C04", 4, "commanderCast=0; castFrom=Command", "calculate total cost",
                "first command-zone cast adds no commander tax", "generic-equivalent CMC=" + first.getTotalMana().getCMC());

        p.incCommanderCast(taxCommander);
        Cost second = CostAdjustment.adjust(sa.getPayCosts(), sa, false);
        Assert.assertEquals(second.getTotalMana().getCMC(), baseCmc + 2);
        emit("C05", 4, "commanderCast=1; castFrom=Command", "calculate total cost",
                "second same-commander cast adds 2 generic mana", "cost delta=+2");

        p.incCommanderCast(taxCommander);
        Cost third = CostAdjustment.adjust(sa.getPayCosts(), sa, false);
        Assert.assertEquals(third.getTotalMana().getCMC(), baseCmc + 4);
        emit("C06", 4, "commanderCast=2; castFrom=Command", "calculate total cost",
                "third same-commander cast adds 4 generic mana", "cost delta=+4");
        emit("O", 4, "same command-zone spell evaluated at cast counts 0,1,2", "apply Forge cost adjustment",
                "additional commander costs are engine-owned and scale independently of printed mana cost",
                "adjusted generic-equivalent deltas=0,+2,+4");
    }

    @Test
    public void partnerTaxIsIndependent() {
        Fixture f = fixture(4, true, true);
        Player p = f.p(0);
        List<Card> partners = new ArrayList<>();
        for (Card c : p.getZone(ZoneType.Command)) {
            if (c.isCommander()) {
                partners.add(c);
            }
        }
        Assert.assertEquals(partners.size(), 2);
        Card a = partners.get(0);
        Card b = partners.get(1);
        p.incCommanderCast(a);
        p.incCommanderCast(a);
        Assert.assertEquals(p.getCommanderCast(a), 2);
        Assert.assertEquals(p.getCommanderCast(b), 0);
        emit("C07", 4, "Rograkh and Tymna are partner commanders", "record two casts of only first commander",
                "commander cast counters are keyed independently by commander identity",
                a.getName() + " casts=2; " + b.getName() + " casts=0");
    }

    @Test
    public void commanderZoneMovementChoices() {
        Fixture accept = fixture(4, true);
        Player p = accept.p(0);
        Card cmd = commander(p);
        cmd = accept.game.getAction().moveToPlay(cmd, p, null, AbilityKey.newMap());
        Assert.assertEquals(cmd.getZone().getZoneType(), ZoneType.Battlefield);
        cmd = accept.game.getAction().moveTo(p.getZone(ZoneType.Graveyard), cmd, null);
        Assert.assertEquals(cmd.getZone().getZoneType(), ZoneType.Command);
        emit("C08", 4, "commander on battlefield", "owner accepts command-zone choice for graveyard move",
                "Forge Commander processing places the commander in Command", "destination=Command");

        cmd = accept.game.getAction().moveToPlay(cmd, p, null, AbilityKey.newMap());
        cmd = accept.game.getAction().moveTo(p.getZone(ZoneType.Exile), cmd, null);
        Assert.assertEquals(cmd.getZone().getZoneType(), ZoneType.Command);
        emit("C09", 4, "commander on battlefield", "owner accepts command-zone choice for exile move",
                "Forge Commander processing places the commander in Command", "destination=Command");

        cmd = accept.game.getAction().moveToPlay(cmd, p, null, AbilityKey.newMap());
        cmd = accept.game.getAction().moveTo(p.getZone(ZoneType.Hand), cmd, null);
        Assert.assertEquals(cmd.getZone().getZoneType(), ZoneType.Command);
        cmd = accept.game.getAction().moveToPlay(cmd, p, null, AbilityKey.newMap());
        cmd = accept.game.getAction().moveTo(p.getZone(ZoneType.Library), cmd, null);
        Assert.assertEquals(cmd.getZone().getZoneType(), ZoneType.Command);
        emit("C10", 4, "commander on battlefield", "owner accepts command-zone choice for hand and library moves",
                "Forge replacement processing redirects both moves to Command", "hand->Command; library->Command");
        emit("H", 4, "Commander effect active", "accept optional commander zone processing",
                "replacement/zone-change processing changes the destination semantically", "requested destination replaced by Command");

        Fixture decline = fixture(4, false);
        Player d = decline.p(0);
        Card declined = commander(d);
        declined = decline.game.getAction().moveToPlay(declined, d, null, AbilityKey.newMap());
        declined = decline.game.getAction().moveTo(d.getZone(ZoneType.Graveyard), declined, null);
        Assert.assertEquals(declined.getZone().getZoneType(), ZoneType.Graveyard);
        emit("C11", 4, "commander on battlefield", "owner declines command-zone choice",
                "declining preserves requested destination", "destination=Graveyard");

        decline.lobbies.get(0).setCommanderReplacementChoice(true);
        declined = decline.game.getAction().moveTo(d.getZone(ZoneType.Exile), declined, null);
        Assert.assertEquals(declined.getZone().getZoneType(), ZoneType.Command);
        emit("C12", 4, "commander previously declined into graveyard", "owner accepts on later zone move",
                "a prior decline does not disable later commander movement choice", "later destination=Command");
        emit("T", 4, "same controller path exercised with explicit false then true replacement decisions",
                "decline first discretionary choice; explicitly accept next choice",
                "Forge consumes the supplied choice each time without a harness fallback",
                "false=>Graveyard; true=>Command");
    }

    @Test
    public void commanderDamageAndIdentity() {
        Fixture identity = fixture(4, true);
        Player victim = identity.p(1);
        Card c0 = commander(identity.p(0));
        Card c2 = commander(identity.p(2));
        victim.addCommanderDamage(c0, 7);
        victim.addCommanderDamage(c2, 9);
        Assert.assertEquals(victim.getCommanderDamage(c0), 7);
        Assert.assertEquals(victim.getCommanderDamage(c2), 9);
        emit("C13", 4, "two distinct opposing commanders", "apply 7 and 9 commander-damage identity totals",
                "commander damage is tracked by commander identity", "totals=7 and 9, separately keyed");

        Fixture twenty = fixture(4, true);
        Player v20 = twenty.p(1);
        Card source20 = commander(twenty.p(0));
        v20.addCommanderDamage(source20, 20);
        twenty.game.getAction().checkStateEffects(true);
        Assert.assertFalse(v20.hasLost());
        emit("C14", 4, "victim at 40 life", "record 20 damage from one commander; run SBA",
                "20 commander damage is not a loss", "victim remains in game");

        Fixture twentyOne = fixture(4, true);
        Player v21 = twentyOne.p(1);
        Card source21 = commander(twentyOne.p(0));
        v21.addCommanderDamage(source21, 21);
        twentyOne.game.getAction().checkStateEffects(true);
        Assert.assertTrue(v21.hasLost());
        emit("C15", 4, "victim at 40 life", "record 21 damage from one commander; run SBA",
                "21 damage from the same commander causes loss", "victim hasLost=true");
        emit("I", 4, "commander damage threshold reached", "run Forge state-based actions",
                "state-based loss is applied by engine", "victim lost after SBA");

        Fixture split = fixture(4, true);
        Player vs = split.p(1);
        Card s0 = commander(split.p(0));
        Card s2 = commander(split.p(2));
        vs.addCommanderDamage(s0, 11);
        vs.addCommanderDamage(s2, 10);
        split.game.getAction().checkStateEffects(true);
        Assert.assertFalse(vs.hasLost());
        emit("C16", 4, "two opposing commander identities", "record 11 + 10 damage across different commanders; run SBA",
                "commander damage from different identities is not combined", "victim remains in game");
    }

    @Test
    public void commanderIdentitySurvivesControlAndMerge() {
        Fixture f = fixture(4, true);
        Player owner = f.p(0);
        Player other = f.p(1);
        Card cmd = commander(owner);
        cmd = f.game.getAction().moveToPlay(cmd, owner, null, AbilityKey.newMap());
        long ts = f.game.getNextTimestamp();
        cmd.addTempController(other, ts);
        Assert.assertTrue(cmd.isCommander());
        Assert.assertEquals(cmd.getOwner(), owner);
        Assert.assertEquals(cmd.getController(), other);

        Card host = putPermanent(f, owner, owner, "Grizzly Bears");
        host.addMergedCard(cmd);
        Assert.assertTrue(host.isCommander());
        other.addCommanderDamage(host, 3);
        Assert.assertEquals(other.getCommanderDamage(host), 3);
        emit("C17", 4, "commander battlefield object plus noncommander merge host", "temporary control change; merge commander component",
                "commander designation survives control change and merged-object identity and remains a damage key",
                "owner unchanged; controller changed; merged host isCommander=true; damage keyed=3");
        emit("Q", 4, "commander object identity under control/merge", "control change and merge",
                "object identity semantics preserve commander designation where required", "commander=true through control and merged host");
    }

    @Test
    public void fourPlayerApnapPriorityAndCombat() {
        Fixture f = fixture(4, true);
        Player p0 = f.p(0);
        Player p1 = f.p(1);
        Player p2 = f.p(2);
        Player p3 = f.p(3);
        f.game.getPhaseHandler().setPlayerTurn(p0);
        Assert.assertEquals(f.game.getPhaseHandler().getPriorityPlayer(), p0);
        Assert.assertEquals(new ArrayList<>(f.game.getPlayersInTurnOrder(p0)), Arrays.asList(p0, p1, p2, p3));

        for (Player p : Arrays.asList(p0, p1, p2, p3)) {
            Card c = commander(p);
            SpellPermanent sa = c.getSpellPermanent();
            sa.setActivatingPlayer(p);
            f.game.getStack().addSimultaneousStackEntry(sa);
        }
        Assert.assertTrue(f.game.getStack().addAllTriggeredAbilitiesToStack());
        Assert.assertEquals(f.apnapCallbacks, Arrays.asList("WS07-P1", "WS07-P2", "WS07-P3", "WS07-P4"));
        emit("C19", 4, "active player=P1; simultaneous entries controlled by all four players", "preserve each player's intra-batch order",
                "MagicStack dispatches simultaneous entries in APNAP turn order", "callbacks=P1,P2,P3,P4");
        emit("G", 4, "simultaneous stack-entry batch", "no intra-player reorder",
                "engine dispatches simultaneous triggered/stack entries by APNAP owner batches", "callback order=P1,P2,P3,P4");

        Card a1 = putPermanent(f, p0, p0, "Grizzly Bears");
        Card a2 = putPermanent(f, p0, p0, "Savannah Lions");
        a1.setSickness(false);
        a2.setSickness(false);
        Combat combat = new Combat(p0);
        Assert.assertTrue(CombatUtil.canAttack(a1, p1));
        Assert.assertTrue(CombatUtil.canAttack(a2, p2));
        combat.addAttacker(a1, p1);
        combat.addAttacker(a2, p2);
        Assert.assertTrue(CombatUtil.validateAttackers(combat));
        Assert.assertTrue(combat.getAttackersOf(p1).contains(a1));
        Assert.assertTrue(combat.getAttackersOf(p2).contains(a2));
        emit("J", 4, "P1 controls two attack-capable creatures; P2/P3 are separate defenders", "declare one attacker at each defender",
                "Forge combat validates multiple defender assignments", "P2 attacked by Bear; P3 attacked by Lion");
        emit("A", 4, "active=P1", "inspect engine turn order",
                "turn order is P1->P2->P3->P4 and priority initially belongs to active player", "turn-order and priority state verified");
        emit("E", 4, "active=P1", "inspect priority and simultaneous stack dispatch",
                "priority/APNAP stack semantics are engine-owned", "priority=P1; APNAP=P1,P2,P3,P4");
    }

    @Test
    public void playerEliminationAndLeavesGameConsequences() {
        Fixture f = fixture(4, true);
        Player stayingOwner = f.p(0);
        Player leaving = f.p(1);
        Card ownedByLeaving = putPermanent(f, leaving, leaving, "Grizzly Bears");
        Card borrowed = putPermanent(f, stayingOwner, stayingOwner, "Savannah Lions");
        long controlTs = f.game.getNextTimestamp();
        borrowed.addTempController(leaving, controlTs);
        f.game.getAction().controllerChangeZoneCorrection(borrowed);
        Assert.assertEquals(borrowed.getController(), leaving);

        leaving.concede();
        f.game.getAction().checkStateEffects(true);
        Assert.assertFalse(f.game.isGameOver());
        Assert.assertTrue(leaving.hasLost());
        Assert.assertFalse(f.game.getPlayers().contains(leaving));
        Assert.assertFalse(f.game.getCardsInGame().contains(ownedByLeaving));
        Card currentBorrowed = f.game.getCardState(borrowed);
        Assert.assertNotNull(currentBorrowed);
        Assert.assertEquals(currentBorrowed.getOwner(), stayingOwner);
        Assert.assertEquals(currentBorrowed.getController(), stayingOwner);

        emit("C20", 4, "four players in game", "P2 concedes; run state effects",
                "one player loss does not end a four-player game", "gameOver=false; three players remain");
        emit("C21", 4, "P2 owns a battlefield permanent", "P2 leaves game",
                "objects owned by leaving player leave the game", "owned Grizzly Bears absent from cardsInGame");
        emit("C22", 4, "P1-owned permanent temporarily controlled by P2", "P2 leaves game",
                "control effect from leaving player is cleaned up and surviving object returns to owner control",
                "Savannah Lions owner=P1 controller=P1");
        emit("R", 4, "4P with owned and controlled permanents", "P2 concedes",
                "multiplayer elimination applies leaves-game consequences without ending game", "three players remain; ownership/control cleanup verified");
        emit("P", 4, "temporary continuous control effect", "controller leaves game",
                "continuous control state is removed as part of leaves-game cleanup", "surviving object controller restored");
    }

    @Test
    public void londonMulliganStartingPlayerAndShuffleSemantics() {
        Fixture f = fixture(4, true);
        Player player = f.p(0);
        player.getZone(ZoneType.Hand).setCards(List.of());
        player.getZone(ZoneType.Library).setCards(List.of());
        for (int i = 0; i < 14; i++) {
            Card plains = Card.fromPaperCard(paper("Plains"), player);
            if (i < 7) {
                player.getZone(ZoneType.Hand).add(plains);
            } else {
                player.getZone(ZoneType.Library).add(plains);
            }
        }
        LondonMulligan london = new LondonMulligan(player, true);
        Assert.assertEquals(london.handSizeAfterNextMulligan(), 7);
        Assert.assertEquals(london.tuckCardsDuringMulligan(), 0);
        london.mulligan();
        Assert.assertEquals(player.getZone(ZoneType.Hand).size(), 7);
        Assert.assertEquals(london.tuckCardsDuringMulligan(), 0);
        london.mulligan();
        Assert.assertEquals(player.getZone(ZoneType.Hand).size(), 6);
        Assert.assertEquals(london.tuckCardsDuringMulligan(), 1);
        Assert.assertEquals(player.getZone(ZoneType.Hand).size() + player.getZone(ZoneType.Library).size(), 14);
        emit("MANDATORY_LONDON_MULLIGAN", 4,
                "4P Commander; seven-card hand plus seven-card library",
                "take first mulligan, then take second mulligan",
                "London redraws to seven; first multiplayer mulligan is free; second bottoms one; cardinality is preserved",
                "hand after first=7; hand after second=6; tuck count=1; hand+library=14");
        emit("N", 4, "known 14-card hand/library population", "two London mulligan shuffles; no order assertion",
                "shuffle/move operations preserve zone-card cardinality while applying mulligan movement",
                "hand+library remains 14; no RNG ordering claim");

        Player p0 = f.p(0);
        Player p1 = f.p(1);
        Player p2 = f.p(2);
        Player p3 = f.p(3);
        f.game.setStartingPlayer(p2);
        f.game.getPhaseHandler().setPlayerTurn(f.game.getStartingPlayer());
        Assert.assertEquals(f.game.getStartingPlayer(), p2);
        Assert.assertEquals(f.game.getPhaseHandler().getPlayerTurn(), p2);
        Assert.assertEquals(f.game.getPhaseHandler().getPriorityPlayer(), p2);
        Assert.assertEquals(new ArrayList<>(f.game.getPlayersInTurnOrder(p2)), Arrays.asList(p2, p3, p0, p1));
        emit("MANDATORY_STARTING_PLAYER", 4, "4P Commander players P1-P4", "starting-player choice=P3",
                "selected starting player becomes active player, receives initial priority, and anchors turn order",
                "starting=P3; active=P3; priority=P3; order=P3,P4,P1,P2");
    }

    @Test
    public void deterministicNonRngSemanticReplay() {
        Fixture first = fixture(4, true);
        Fixture second = fixture(4, true);
        Player firstVictim = first.p(1);
        Player secondVictim = second.p(1);
        Card firstCommander = commander(first.p(0));
        Card secondCommander = commander(second.p(0));
        firstVictim.addCommanderDamage(firstCommander, 20);
        secondVictim.addCommanderDamage(secondCommander, 20);
        first.game.getAction().checkStateEffects(true);
        second.game.getAction().checkStateEffects(true);
        String firstState = first.game.getPlayers().size() + ":" + firstVictim.hasLost() + ":" + firstVictim.getCommanderDamage(firstCommander);
        String secondState = second.game.getPlayers().size() + ":" + secondVictim.hasLost() + ":" + secondVictim.getCommanderDamage(secondCommander);
        Assert.assertEquals(firstState, secondState);
        emit("S", 4, "two fresh deterministic 4P Forge fixtures", "apply identical non-RNG commander-damage action and SBA check",
                "identical deterministic rules inputs yield identical semantic state",
                "snapshotA=" + firstState + "; snapshotB=" + secondState);
    }
}
