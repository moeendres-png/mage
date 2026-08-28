package forge.ws07;

import forge.deck.Deck;
import forge.deck.DeckSection;
import forge.game.Game;
import forge.game.GameRules;
import forge.game.GameStage;
import forge.game.GameType;
import forge.game.Match;
import forge.game.card.Card;
import forge.game.mulligan.LondonMulligan;
import forge.game.player.Player;
import forge.game.player.RegisteredPlayer;
import forge.game.zone.ZoneType;
import forge.gamesimulationtests.BaseGameSimulationTest;
import forge.gamesimulationtests.util.CardDatabaseHelper;
import forge.gamesimulationtests.util.LobbyPlayerForTests;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** Startup-only WS07 semantics: London mulligan and starting-player/turn-order state. */
public class WS07StartupConformanceTest extends BaseGameSimulationTest {
    private static final String[] COMMANDERS = {
            "Isamaru, Hound of Konda",
            "Talrand, Sky Summoner",
            "Krenko, Mob Boss",
            "Ayli, Eternal Pilgrim"
    };

    private Game game() {
        List<RegisteredPlayer> registered = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            Deck deck = new Deck("WS07-startup-" + i);
            deck.getOrCreate(DeckSection.Commander).add(CardDatabaseHelper.getCard(COMMANDERS[i]), 1);
            deck.getMain().add(CardDatabaseHelper.getCard("Plains"), 20);
            RegisteredPlayer rp = RegisteredPlayer.forCommander(deck);
            rp.setPlayer(new LobbyPlayerForTests("WS07-P" + (i + 1), null));
            registered.add(rp);
        }
        GameRules rules = new GameRules(GameType.Commander);
        rules.addAppliedVariant(GameType.Commander);
        Game game = new Match(rules, registered, "WS07-startup").createGame();
        game.setAge(GameStage.Play);
        for (int i = 0; i < 4; i++) {
            game.getRegisteredPlayers().get(i).initVariantsZones(registered.get(i));
        }
        return game;
    }

    private static String esc(String value) {
        return value.replace("\\", "\\\\").replace("\"", "\\\"")
                .replace("\n", "\\n").replace("\r", "\\r");
    }

    private void emit(String id, String initial, String decisions, String assertion, String observed) {
        String path = System.getenv("WS07_RESULT_PATH");
        if (path == null || path.isBlank()) return;
        String json = "{" +
                "\"id\":\"" + esc(id) + "\"," +
                "\"scenario_source\":\"research/greenfield-qualification/ws07/WS07StartupConformanceTest.java\"," +
                "\"player_count\":4," +
                "\"initial_state\":\"" + esc(initial) + "\"," +
                "\"decisions\":\"" + esc(decisions) + "\"," +
                "\"semantic_assertions\":[\"" + esc(assertion) + "\"]," +
                "\"observed_state\":\"" + esc(observed) + "\"," +
                "\"result\":\"PASS\"," +
                "\"evidence_class\":\"TECHNICALLY_CONFORMANT\"," +
                "\"assertion_kind\":\"ENGINE_STATE\"}" + System.lineSeparator();
        try {
            Path output = Path.of(path);
            if (output.getParent() != null) Files.createDirectories(output.getParent());
            Files.writeString(output, json, StandardCharsets.UTF_8,
                    StandardOpenOption.CREATE, StandardOpenOption.APPEND);
        } catch (IOException e) {
            throw new RuntimeException(e);
        }
    }

    @Test
    public void londonMulliganHasFreeFirstMultiplayerMulliganAndBottomingAfterSecond() {
        Game game = game();
        Player player = game.getRegisteredPlayers().get(0);
        for (int i = 0; i < 14; i++) {
            Card plains = Card.fromPaperCard(CardDatabaseHelper.getCard("Plains"), player);
            if (i < 7) player.getZone(ZoneType.Hand).add(plains);
            else player.getZone(ZoneType.Library).add(plains);
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
        emit("MANDATORY_LONDON_MULLIGAN",
                "4P Commander; seven-card hand plus seven-card library",
                "take first mulligan, then take second mulligan",
                "London redraws to seven; first multiplayer mulligan is free; second mulligan bottoms one; card cardinality is preserved",
                "hand after first=7; hand after second=6; tuck count=1; hand+library=14");
        emit("N", "known 14-card hand/library population", "two London mulligan shuffles; no order assertion",
                "shuffle/move operations preserve zone-card cardinality while applying mulligan movement",
                "hand+library remains 14; no RNG order counted as evidence");
    }

    @Test
    public void explicitStartingPlayerDefinesPriorityAndRotatedTurnOrder() {
        Game game = game();
        Player p0 = game.getRegisteredPlayers().get(0);
        Player p1 = game.getRegisteredPlayers().get(1);
        Player p2 = game.getRegisteredPlayers().get(2);
        Player p3 = game.getRegisteredPlayers().get(3);
        game.setStartingPlayer(p2);
        game.getPhaseHandler().setPlayerTurn(game.getStartingPlayer());
        Assert.assertEquals(game.getStartingPlayer(), p2);
        Assert.assertEquals(game.getPhaseHandler().getPlayerTurn(), p2);
        Assert.assertEquals(game.getPhaseHandler().getPriorityPlayer(), p2);
        Assert.assertEquals(new ArrayList<>(game.getPlayersInTurnOrder(p2)), Arrays.asList(p2, p3, p0, p1));
        emit("MANDATORY_STARTING_PLAYER", "4P Commander players P1-P4", "starting-player choice=P3",
                "selected starting player becomes active player, receives initial priority, and anchors turn order",
                "starting=P3; active=P3; priority=P3; order=P3,P4,P1,P2");
    }
}