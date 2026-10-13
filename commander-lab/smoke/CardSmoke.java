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
            String engineName = engineName(card);
            if (!engineName.equals(card)) {
                row.addProperty("engine_name", engineName);
            }
            try {
                smoke(engineName, "smoke-" + (i++), row);
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

    /**
     * XMage stores names ASCII-folded (Grishnakh, Lord of the Nazgul) and names a prepare card by
     * its creature face only; decklists and Scryfall use the printed name and "Front // Spell".
     */
    static String engineName(String card) {
        String folded = java.text.Normalizer.normalize(card, java.text.Normalizer.Form.NFD)
                .replaceAll("\\p{M}", "");
        mage.cards.repository.CardInfo info = mage.cards.repository.CardRepository.instance.findCard(folded, true);
        return info == null ? card : info.getName();
    }

    /** Spells P1 casts first, so a card that needs a spell on the stack has one to answer. */
    static final java.util.Map<String, String> BAIT = java.util.Map.of(
            "stack-creature", "Grizzly Bears",
            "stack-noncreature", "Divination",
            "stack-instant", "Shock");
    static final String[] VARIANTS = {"stack-creature", "stack-noncreature", "stack-instant", "combat"};

    static void smoke(String card, String tag, JsonObject row) {
        smoke(card, tag, row, Zone.HAND, "plain");
        for (String variant : VARIANTS) {
            if (!"NOT_OFFERED".equals(row.has("status") ? row.get("status").getAsString() : "")) break;
            JsonObject retry = new JsonObject();
            try {
                smoke(card, tag + "-" + variant, retry, Zone.HAND, variant);
            } catch (Throwable e) {
                retry.addProperty("status", "HARNESS_ERROR");
                retry.addProperty("detail", String.valueOf(e).replace('\n', ' '));
            }
            if (!"NOT_OFFERED".equals(retry.has("status") ? retry.get("status").getAsString() : "")) {
                for (String key : retry.keySet()) row.add(key, retry.get(key));
                row.addProperty("variant", variant);
            }
        }
        if ("BATTLEFIELD".equals(row.has("zone") ? row.get("zone").getAsString() : "")) {
            JsonObject placed = new JsonObject();
            try {
                smoke(card, tag + "-bf", placed, Zone.BATTLEFIELD, "plain");
            } catch (Throwable e) {
                placed.addProperty("status", "HARNESS_ERROR");
                placed.addProperty("detail", String.valueOf(e).replace('\n', ' '));
            }
            row.add("on_battlefield", placed);
        }
    }

    static void smoke(String card, String tag, JsonObject row, Zone start, String variant) {
        List<XmageNativeStateRestoration.RequestedObject> objects = new ArrayList<>();
        objects.add(XmageMultiplayerScenario.obj("P1", card, 0, start));
        int n = 0;
        for (String basic : BASICS) {
            for (int k = 0; k < 6; k++) {
                objects.add(XmageMultiplayerScenario.obj("P1", basic, n++, Zone.BATTLEFIELD));
            }
        }
        objects.add(XmageMultiplayerScenario.obj("P1", "Grizzly Bears", 100, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P1", "Grizzly Bears", 101, Zone.GRAVEYARD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Grizzly Bears", 0, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Ornithopter", 1, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Forest", 2, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Grizzly Bears", 3, Zone.GRAVEYARD));
        // Targets for color-, type- and graveyard-restricted cards.
        objects.add(XmageMultiplayerScenario.obj("P2", "Walking Corpse", 4, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Raging Goblin", 5, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Savannah Lions", 6, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Watchwolf", 7, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Mind Stone", 8, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P2", "Glorious Anthem", 9, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P1", "Ornithopter", 102, Zone.GRAVEYARD));
        objects.add(XmageMultiplayerScenario.obj("P1", "Lightning Bolt", 103, Zone.GRAVEYARD));
        objects.add(XmageMultiplayerScenario.obj("P1", "Mind Stone", 104, Zone.BATTLEFIELD));
        objects.add(XmageMultiplayerScenario.obj("P1", "Isamaru, Hound of Konda", 106, Zone.BATTLEFIELD));
        if (BAIT.containsKey(variant)) {
            objects.add(XmageMultiplayerScenario.obj("P1", BAIT.get(variant), 105, Zone.HAND));
        }
        XmageMultiplayerScenario s = XmageMultiplayerScenario.start(tag, 2, "P1", objects);
        try {
            if (start == Zone.BATTLEFIELD) {
                activations(card, s, row);
                row.addProperty("status", "PLACED");
            } else if (prepare(variant, s, row)) {
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
                s.session.submitAction(choose(s.session.legalActionsPayload()));
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
                JsonObject ch = choose(l2);
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
        List<JsonObject> offers = new ArrayList<>(XmageExternalRiskSignalTest.spellOffers(legal, card));
        if (offers.isEmpty() && card.contains(" // ")) {
            // split and adventure-style cards are offered per half
            for (String half : card.split(" // ")) {
                offers.addAll(XmageExternalRiskSignalTest.spellOffers(legal, half));
            }
        }
        if (!offers.isEmpty()) {
            offers.sort(java.util.Comparator.comparing(FullGameTestPilot::key));
            // the scenario's commander may share the name (Rograkh): cast the copy from hand
            offers.sort(java.util.Comparator.comparing((JsonObject a) -> {
                JsonObject m = a.getAsJsonObject("metadata").getAsJsonObject("xmage_option_metadata");
                return m != null && m.has("source_object_id")
                        && p1.getHand().contains(UUID.fromString(m.get("source_object_id").getAsString())) ? 0 : 1;
            }));
            offer = offers.get(0);
            row.addProperty("offers", offers.size());
            // track the copy the offer casts, not another copy of the same card in hand
            JsonObject md = offer.getAsJsonObject("metadata").getAsJsonObject("xmage_option_metadata");
            if (md != null && md.has("source_object_id")) {
                UUID offered = UUID.fromString(md.get("source_object_id").getAsString());
                if (p1.getHand().contains(offered)) {
                    cardId = offered;
                }
            }
        } else {
            for (JsonElement e : legal.getAsJsonArray("actions")) {
                JsonObject a = e.getAsJsonObject();
                if (FullGameTestPilot.label(a).contains("Play " + card)) offer = a;
            }
            if (offer == null) {
                if (System.getenv("SMOKE_DEBUG") != null) {
                    for (JsonElement e : legal.getAsJsonArray("actions")) {
                        System.out.println("DBGO " + FullGameTestPilot.label(e.getAsJsonObject()) + " :: "
                                + e.getAsJsonObject().getAsJsonObject("metadata").get("xmage_option_metadata"));
                    }
                }
                row.addProperty("status", "NOT_OFFERED");
                return;
            }
            row.addProperty("land", true);
        }
        s.session.submitAction(FullGameTestPilot.proposal(legal, offer));
        List<String> classes = new ArrayList<>();
        boolean left = false;
        boolean wasOnStack = false;
        for (int d = 0; d < 200; d++) {
            JsonObject pending = s.session.pendingDecisionPayload();
            if (pending.has("failure") && !pending.get("failure").isJsonNull()) {
                row.addProperty("status", "ABORT");
                row.add("failure", pending.get("failure"));
                row.addProperty("decisions", String.join(",", classes));
                return;
            }
            Zone zone = game.getState().getZone(cardId);
            if (zone == Zone.STACK) {
                wasOnStack = true;
            }
            if (zone != Zone.HAND && zone != Zone.STACK) {
                left = true;
            }
            // a spell that returns itself to its owner's hand (Cerebral Eruption) also resolved
            if (game.getStack().isEmpty() && (left || (wasOnStack && zone == Zone.HAND))) {
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
            s.session.submitAction(choose(l));
        }
        Zone zone = game.getState().getZone(cardId);
        row.addProperty("status", zone == Zone.HAND ? "NOT_CAST" : "STUCK");
        row.addProperty("zone", String.valueOf(zone));
        row.addProperty("decisions", String.join(",", classes.subList(Math.max(0, classes.size() - 20), classes.size())));
    }

    /**
     * FullGameTestPilot.choose plus what it leaves out: a multi-select decision gets its minimum
     * number of options (smallest semantic keys of the same option type), and a target_amount
     * decision assigns everything that remains to the chosen target.
     */
    static JsonObject choose(JsonObject legal) {
        JsonObject proposal = FullGameTestPilot.choose(legal);
        JsonObject choices = proposal.getAsJsonObject("choices");
        List<JsonObject> actions = new ArrayList<>();
        legal.getAsJsonArray("actions").forEach(e -> actions.add(e.getAsJsonObject()));
        actions.sort(java.util.Comparator.comparing(FullGameTestPilot::key));
        String chosenId = proposal.get("legal_action_id").getAsString();
        JsonObject chosen = actions.stream()
                .filter(a -> chosenId.equals(a.get("action_id").getAsString())).findFirst().orElse(null);
        if (chosen == null) return proposal;
        JsonObject md = chosen.getAsJsonObject("metadata");
        int min = md.has("minimum_selections") ? md.get("minimum_selections").getAsInt() : 1;
        if (min > 1 && !choices.has("selected_option_ids")) {
            com.google.gson.JsonArray ids = new com.google.gson.JsonArray();
            ids.add(optionId(chosen));
            for (JsonObject a : actions) {
                if (ids.size() >= min) break;
                if (a == chosen || !FullGameTestPilot.type(a).equals(FullGameTestPilot.type(chosen))) continue;
                ids.add(optionId(a));
            }
            choices.add("selected_option_ids", ids);
        }
        JsonObject context = legal.getAsJsonObject("decision").getAsJsonObject("context");
        if ("target_amount".equals(legal.get("decision_class").getAsString())
                && context.has("numeric_max") && !choices.has("numeric_choice")
                && !choices.has("numeric_choices")) {
            choices.addProperty("numeric_choice", context.get("numeric_max").getAsInt());
        }
        return proposal;
    }

    static String optionId(JsonObject action) {
        String id = action.get("action_id").getAsString();
        return id.substring(id.indexOf(':') + 1);
    }

    /**
     * Bring the position to where the card can be cast: with a bait spell of P1 on the stack, or
     * with P1's Grizzly Bears attacking. Returns false (and records why) when it cannot.
     */
    static boolean prepare(String variant, XmageMultiplayerScenario s, JsonObject row) {
        if ("plain".equals(variant)) return true;
        Game game = s.session.restorationGame();
        if (BAIT.containsKey(variant)) {
            JsonObject legal = s.session.legalActionsPayload();
            List<JsonObject> offers = XmageExternalRiskSignalTest.spellOffers(legal, BAIT.get(variant));
            if (offers.isEmpty()) { row.addProperty("status", "VARIANT_SETUP_FAILED"); return false; }
            s.session.submitAction(FullGameTestPilot.proposal(legal, offers.get(0)));
            for (int d = 0; d < 60; d++) {
                if (!game.getStack().isEmpty() && "priority".equals(s.decisionClass()) && "P1".equals(s.actor())) {
                    return true;
                }
                JsonObject pending = s.session.pendingDecisionPayload();
                if (pending.get("decision") == null || pending.get("decision").isJsonNull()) break;
                s.session.submitAction(choose(s.session.legalActionsPayload()));
            }
            row.addProperty("status", "VARIANT_SETUP_FAILED");
            return false;
        }
        // combat: pass to declare attackers, attack P2 with P1's Grizzly Bears
        for (int d = 0; d < 40; d++) {
            if (!game.getCombat().getAttackers().isEmpty() && "priority".equals(s.decisionClass())
                    && "P1".equals(s.actor())) {
                return true;
            }
            JsonObject pending = s.session.pendingDecisionPayload();
            if (pending.get("decision") == null || pending.get("decision").isJsonNull()) break;
            JsonObject legal = s.session.legalActionsPayload();
            String cls = legal.get("decision_class").getAsString();
            JsonObject pick = null;
            if ("declare_attacker".equals(cls)) {
                for (JsonElement e : legal.getAsJsonArray("actions")) {
                    if (FullGameTestPilot.label(e.getAsJsonObject()).startsWith("Grizzly Bears attacks")) {
                        pick = e.getAsJsonObject();
                        break;
                    }
                }
            } else if ("priority".equals(cls) && "P1".equals(s.actor())) {
                for (JsonElement e : legal.getAsJsonArray("actions")) {
                    if ("pass_priority".equals(FullGameTestPilot.type(e.getAsJsonObject()))) {
                        pick = e.getAsJsonObject();
                        break;
                    }
                }
            }
            JsonObject submit = pick == null ? choose(legal) : FullGameTestPilot.proposal(legal, pick);
            if (System.getenv("SMOKE_DEBUG") != null) {
                String picked = "";
                for (JsonElement e : legal.getAsJsonArray("actions")) {
                    if (e.getAsJsonObject().get("action_id").getAsString().equals(submit.get("legal_action_id").getAsString())) {
                        picked = FullGameTestPilot.label(e.getAsJsonObject());
                    }
                }
                System.out.println("DBGC " + cls + " " + s.actor() + " " + game.getTurnStepType() + " -> " + picked);
            }
            s.session.submitAction(submit);
        }
        row.addProperty("status", "VARIANT_SETUP_FAILED");
        return false;
    }
}
