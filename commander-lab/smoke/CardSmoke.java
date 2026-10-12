package org.commanderlab.xmage;

import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import mage.cards.Card;
import mage.constants.Zone;
import mage.game.Game;
import mage.players.Player;

import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Scratch prototype: cast each card once in a prepared 2P position and record the outcome. */
public final class CardSmoke {
    static final String[] BASICS = {"Plains", "Island", "Swamp", "Mountain", "Forest"};

    public static void main(String[] args) throws Exception {
        List<String> cards = Files.readAllLines(Path.of(args[0]));
        Path out = Path.of(args[1]);
        int i = 0;
        for (String card : cards) {
            if (card.isBlank()) continue;
            long t = System.currentTimeMillis();
            JsonObject row = new JsonObject();
            row.addProperty("card", card);
            try {
                smoke(card, "smoke-" + (i++), row);
            } catch (Throwable e) {
                row.addProperty("status", "HARNESS_ERROR");
                row.addProperty("detail", String.valueOf(e).replace('\n', ' '));
            }
            row.addProperty("ms", System.currentTimeMillis() - t);
            Files.writeString(out, row + "\n", StandardOpenOption.CREATE, StandardOpenOption.APPEND);
            System.out.println(row);
        }
        System.exit(0);
    }

    static void smoke(String card, String tag, JsonObject row) {
        smoke(card, tag, row, Zone.HAND);
        if ("BATTLEFIELD".equals(row.has("zone") ? row.get("zone").getAsString() : "")) {
            JsonObject placed = new JsonObject();
            try {
                smoke(card, tag + "-bf", placed, Zone.BATTLEFIELD);
            } catch (Throwable e) {
                placed.addProperty("status", "HARNESS_ERROR");
                placed.addProperty("detail", String.valueOf(e).replace('\n', ' '));
            }
            row.add("on_battlefield", placed);
        }
    }

    static void smoke(String card, String tag, JsonObject row, Zone start) {
        List<XmageNativeStateRestoration.RequestedObject> objects = new ArrayList<>();
        objects.add(XmageMultiplayerScenario.obj("P1", card, 0, start));
        int n = 0;
        for (String basic : BASICS) {
            for (int k = 0; k < 4; k++) {
                objects.add(XmageMultiplayerScenario.obj("P1", basic, n++, Zone.BATTLEFIELD));
            }
        }
        objects.add(XmageMultiplayerScenario.obj("P1", "Grizzly Bears", 100, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P1", "Grizzly Bears", 101, Zone.GRAVEYARD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Grizzly Bears", 0, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Ornithopter", 1, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Forest", 2, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Grizzly Bears", 3, Zone.GRAVEYARD));
        XmageMultiplayerScenario s = XmageMultiplayerScenario.start(tag, 2, "P1", objects);
        try {
            if (start == Zone.BATTLEFIELD) {
                activations(card, s, row);
                row.addProperty("status", "PLACED");
            } else {
                run(card, s, row);
            }
        } finally {
            try { s.session.shutdownGame(); } catch (Throwable ignored) { }
        }
    }

    /** Try each non-spell ability of the card the engine offers at P1's priority, once each. */
    static void activations(String card, XmageMultiplayerScenario s, JsonObject row) {
        com.google.gson.JsonArray results = new com.google.gson.JsonArray();
        java.util.Set<String> tried = new java.util.HashSet<>();
        for (int round = 0; round < 6; round++) {
            JsonObject pending = s.session.pendingDecisionPayload();
            if (pending.has("failure") && !pending.get("failure").isJsonNull()) break;
            if (!"priority".equals(s.decisionClass()) || !"P1".equals(s.actor())) {
                // let the opponent pass back
                if (pending.get("decision") == null || pending.get("decision").isJsonNull()) break;
                s.session.submitAction(FullGameTestPilot.choose(s.session.legalActionsPayload()));
                continue;
            }
            JsonObject legal = s.session.legalActionsPayload();
            JsonObject pick = null;
            List<JsonObject> ordered = new ArrayList<>();
            legal.getAsJsonArray("actions").forEach(e -> ordered.add(e.getAsJsonObject()));
            ordered.sort(java.util.Comparator.comparing((JsonObject a) -> {
                String l = FullGameTestPilot.label(a);
                return (l.contains("Return {this}") || l.contains("Sacrifice {this}") || l.contains("Exile {this}")) ? 1 : 0;
            }));
            for (JsonObject a : ordered) {
                JsonObject md = a.getAsJsonObject("metadata").getAsJsonObject("xmage_option_metadata");
                if (md == null || !md.has("source_name") || !card.equals(md.get("source_name").getAsString())) continue;
                String type = md.has("ability_type") ? md.get("ability_type").getAsString() : "";
                if ("spell".equals(type)) continue;
                String key = FullGameTestPilot.label(a);
                if (tried.add(key)) { pick = a; break; }
            }
            if (pick == null) break;
            JsonObject r = new JsonObject();
            r.addProperty("ability", FullGameTestPilot.label(pick));
            s.session.submitAction(FullGameTestPilot.proposal(legal, pick));
            String outcome = "OK";
            for (int d = 0; d < 150; d++) {
                JsonObject p = s.session.pendingDecisionPayload();
                if (p.has("failure") && !p.get("failure").isJsonNull()) {
                    outcome = "ABORT " + p.get("failure");
                    break;
                }
                Game game = s.session.restorationGame();
                if (game.getStack().isEmpty() && "priority".equals(s.decisionClass()) && "P1".equals(s.actor())) break;
                if (p.get("decision") == null || p.get("decision").isJsonNull()) { outcome = "NO_DECISION"; break; }
                JsonObject l2 = s.session.legalActionsPayload();
                JsonObject ch = FullGameTestPilot.choose(l2);
                if (System.getenv("SMOKE_DEBUG") != null) {
                    String picked = "";
                    for (JsonElement e : l2.getAsJsonArray("actions")) if (e.getAsJsonObject().get("action_id").getAsString().equals(ch.get("legal_action_id").getAsString())) picked = FullGameTestPilot.label(e.getAsJsonObject());
                    System.out.println("DBGA " + l2.get("decision_class").getAsString() + " " + s.prompt().replaceAll("<[^>]*>", "") + " -> " + picked);
                }
                s.session.submitAction(ch);
                if (d == 149) outcome = "STUCK";
            }
            r.addProperty("outcome", outcome);
            results.add(r);
            if (!outcome.equals("OK")) break;
        }
        row.add("abilities", results);
    }

    static void run(String card, XmageMultiplayerScenario s, JsonObject row) {
        Game game = s.session.restorationGame();
        Player p1 = s.seats.get("P1");
        UUID cardId = null;
        for (Card c : p1.getHand().getCards(game)) {
            if (card.equals(c.getName())) cardId = c.getId();
        }
        if (cardId == null) { row.addProperty("status", "NOT_IN_HAND"); return; }
        JsonObject legal = s.session.legalActionsPayload();
        JsonObject offer = null;
        List<JsonObject> offers = XmageExternalRiskSignalTest.spellOffers(legal, card);
        if (!offers.isEmpty()) {
            offers.sort(java.util.Comparator.comparing(FullGameTestPilot::key));
            offer = offers.get(0);
            row.addProperty("offers", offers.size());
        } else {
            for (JsonElement e : legal.getAsJsonArray("actions")) {
                JsonObject a = e.getAsJsonObject();
                if (FullGameTestPilot.label(a).contains("Play " + card)) offer = a;
            }
            if (offer == null) { row.addProperty("status", "NOT_OFFERED"); return; }
            row.addProperty("land", true);
        }
        s.session.submitAction(FullGameTestPilot.proposal(legal, offer));
        List<String> classes = new ArrayList<>();
        boolean left = false;
        for (int d = 0; d < 200; d++) {
            JsonObject pending = s.session.pendingDecisionPayload();
            if (pending.has("failure") && !pending.get("failure").isJsonNull()) {
                row.addProperty("status", "ABORT");
                row.add("failure", pending.get("failure"));
                row.addProperty("decisions", String.join(",", classes));
                return;
            }
            Zone zone = game.getState().getZone(cardId);
            if (zone != Zone.HAND && zone != Zone.STACK) {
                left = true;
            }
            if (game.getStack().isEmpty() && left) {
                row.addProperty("status", "RESOLVED");
                row.addProperty("zone", String.valueOf(zone));
                row.addProperty("decisions", String.join(",", classes));
                if (zone == Zone.BATTLEFIELD) {
                    activations(card, s, row);
                }
                return;
            }
            if (pending.get("decision") == null || pending.get("decision").isJsonNull()) {
                row.addProperty("status", "NO_DECISION");
                return;
            }
            JsonObject l = s.session.legalActionsPayload();
            classes.add(l.get("decision_class").getAsString());
            if (System.getenv("SMOKE_DEBUG") != null && d < 30) {
                StringBuilder sb = new StringBuilder("DBG " + l.get("decision_class").getAsString() + " " + s.prompt() + " pool=" + game.getPlayer(game.getActivePlayerId()).getManaPool().getMana() + " ::");
                for (JsonElement e : l.getAsJsonArray("actions")) {
                    JsonObject md = e.getAsJsonObject().getAsJsonObject("metadata");
                    sb.append(" [").append(FullGameTestPilot.label(e.getAsJsonObject()));
                    JsonObject x = md.getAsJsonObject("xmage_option_metadata");
                    if (x != null && x.has("advances_payment")) sb.append(" adv=").append(x.get("advances_payment"));
                    sb.append("]");
                }
                System.out.println(sb);
            }
            s.session.submitAction(FullGameTestPilot.choose(l));
        }
        Zone zone = game.getState().getZone(cardId);
        row.addProperty("status", zone == Zone.HAND ? "NOT_CAST" : "STUCK");
        row.addProperty("zone", String.valueOf(zone));
        row.addProperty("decisions", String.join(",", classes.subList(Math.max(0, classes.size() - 20), classes.size())));
    }
}
