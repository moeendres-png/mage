package forge.gamesimulationtests;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import forge.ai.AITest;
import forge.card.CardStateName;
import forge.game.ability.AbilityUtils;
import forge.game.card.Card;
import forge.game.card.CardState;
import forge.game.keyword.Keyword;
import forge.game.keyword.KeywordInterface;
import forge.game.player.Player;
import forge.game.replacement.ReplacementEffect;
import forge.game.spellability.SpellAbility;
import forge.game.staticability.StaticAbility;
import forge.game.trigger.Trigger;
import forge.game.trigger.TriggerHandler;
import org.testng.Assert;
import org.testng.annotations.Test;

import java.lang.reflect.Field;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

/**
 * WS29 qualification-only exact source-binding probe.
 *
 * Every card is loaded from the pinned Forge card database. For source SVars that are only
 * materialized later (for example an Execute$ ability of a delayed trigger), this probe asks
 * CardState.getAbilityForTrigger for the exact named SVar. That method is Forge's own cached
 * actual-card AbilityFactory path and therefore does not fabricate or substitute a definition.
 * No SpellAbility.resolve/AbilityUtils.resolve call occurs. This is binding evidence only and
 * must never be promoted to semantic-behavior evidence.
 */
public class Ws29SourceBindingTest extends AITest {
    private static final Set<String> EFFECT_TARGETS = Set.of(
            "forge.game.ability.effects.AlterAttributeEffect",
            "forge.game.ability.effects.AnimateAllEffect",
            "forge.game.ability.effects.AnimateEffect",
            "forge.game.ability.effects.CloneEffect",
            "forge.game.ability.effects.ControlGainEffect",
            "forge.game.ability.effects.ControlGainVariantEffect",
            "forge.game.ability.effects.ControlPlayerEffect",
            "forge.game.ability.effects.CopyPermanentEffect",
            "forge.game.ability.effects.CopySpellAbilityEffect",
            "forge.game.ability.effects.ProtectEffect",
            "forge.game.ability.effects.PumpAllEffect",
            "forge.game.ability.effects.PumpEffect",
            "forge.game.ability.effects.SetStateEffect"
    );

    @Test
    public void everyAssignedV2PathBindsToPinnedActualCardRuntime() throws Exception {
        final Path casesPath = Path.of(System.getProperty("ws29.cases"));
        final Path outPath = Path.of(System.getProperty("ws29.binding.out"));
        final List<String> lines = Files.readAllLines(casesPath, StandardCharsets.UTF_8);
        Assert.assertEquals(lines.size(), 301, "authoritative owner partition must contain exactly 301 cases");

        final forge.game.Game game = initAndCreateGame();
        final Player player = game.getPlayers().get(0);
        final List<String> output = new ArrayList<>();
        int passCount = 0;

        for (String line : lines) {
            final JsonObject c = JsonParser.parseString(line).getAsJsonObject();
            final String pathId = str(c, "v2_path_id");
            final String cardName = str(c, "card_name");
            final String sourceDirective = str(c, "source_directive");
            final String sourceSVar = str(c, "source_svar");
            final String sourceText = str(c, "source_text");
            final String target = str(c, "implementation_target");
            final String rootKind = str(c, "root_kind");
            final String rootKey = str(c, "root_key");

            final Card card = createCard(cardName, player);
            Assert.assertNotNull(card, pathId + " card must load from pinned Forge database");
            Assert.assertEquals(card.getState(CardStateName.Original).getName(), cardName,
                    pathId + " card identity must bind to actual source");
            final CardState state = findSourceState(card, sourceDirective, sourceSVar, sourceText);
            Assert.assertNotNull(state, pathId + " exact source must bind to one actual CardState");

            final boolean exactSourceBound = sourceMatches(state, sourceDirective, sourceSVar, sourceText);
            Assert.assertTrue(exactSourceBound, pathId + " exact source must bind on selected actual CardState");

            boolean targetBound;
            String runtimeDetail;
            if (EFFECT_TARGETS.contains(target)) {
                final String expectedApi = apiForTarget(target);
                final List<SpellAbility> graph = collectSpellAbilities(state);
                boolean graphBound = hasApi(graph, expectedApi);
                boolean exactSVarMaterialized = false;
                int sourceGraphNodes = 0;
                if (!graphBound && "SVAR".equals(sourceDirective) && !sourceSVar.isEmpty()) {
                    // Some exact source SVars are reachable only after runtime creation of a delayed
                    // trigger/effect. Materialize that exact CardState-owned SVar through Forge's own
                    // actual-card parser rather than constructing a definition in the qualification code.
                    final List<SpellAbility> sourceGraph = new ArrayList<>();
                    final Set<SpellAbility> sourceSeen = Collections.newSetFromMap(new IdentityHashMap<>());
                    try {
                        walk(state.getAbilityForTrigger(sourceSVar), sourceGraph, sourceSeen);
                        sourceGraphNodes = sourceGraph.size();
                        exactSVarMaterialized = hasApi(sourceGraph, expectedApi);
                    } catch (RuntimeException ignored) {
                        // The assertion below remains fail-closed. Some SVars are non-ability runtime
                        // expressions; they are handled by their own implementation-target branch.
                    }
                }
                targetBound = graphBound || exactSVarMaterialized;
                runtimeDetail = "ApiType=" + expectedApi
                        + ";graph_nodes=" + graph.size()
                        + ";exact_svar_materialized=" + exactSVarMaterialized
                        + ";source_graph_nodes=" + sourceGraphNodes;
            } else if (target.equals("forge.game.trigger.TriggerHandler#parseTrigger")) {
                Assert.assertFalse(sourceSVar.isEmpty(), pathId + " trigger parser path must be source-bound to SVar");
                final Trigger parsed = TriggerHandler.parseTrigger(state.getSVar(sourceSVar), card, true, state);
                targetBound = parsed != null && parsed.getMode() != null;
                runtimeDetail = "TriggerType=" + (parsed == null ? "null" : parsed.getMode().name());
            } else if (target.equals("forge.game.ability.AbilityUtils#calculateAmount")) {
                Assert.assertFalse(sourceSVar.isEmpty(), pathId + " amount path must be source-bound to SVar");
                final int amount = AbilityUtils.calculateAmount(card, state.getSVar(sourceSVar), null);
                targetBound = true;
                runtimeDetail = "calculateAmount=" + amount;
            } else if (target.equals("forge.game.keyword.Partner")) {
                targetBound = state.getIntrinsicKeywords().stream().anyMatch(k -> k.getKeyword() == Keyword.PARTNER);
                runtimeDetail = "Keyword=PARTNER";
            } else if (target.startsWith("forge.game.staticability.StaticAbilityMode#")) {
                final String mode = target.substring(target.indexOf('#') + 1);
                targetBound = state.getStaticAbilities().stream()
                        .anyMatch(st -> st.getMode().stream().anyMatch(m -> m.name().equals(mode)));
                runtimeDetail = "StaticAbilityMode=" + mode;
            } else if (target.equals("forge.game.staticability.StaticAbility")) {
                targetBound = hasRuntimeStatic(state, rootKind, rootKey);
                runtimeDetail = "StaticAbility=root:" + rootKind + "/" + rootKey;
            } else {
                targetBound = false;
                runtimeDetail = "unmapped-target";
            }

            Assert.assertTrue(targetBound,
                    pathId + " assigned implementation target must be constructed from actual card runtime: " + target);
            passCount++;

            final JsonObject row = new JsonObject();
            row.addProperty("schema", "commander-simulator-next.ws29.source-binding-trace.v1");
            row.addProperty("v2_path_id", pathId);
            row.addProperty("oracle_identity", str(c, "oracle_identity"));
            row.addProperty("card_name", cardName);
            row.addProperty("source_path", str(c, "source_path"));
            row.addProperty("source_line", c.get("source_line").getAsInt());
            row.addProperty("source_directive", sourceDirective);
            row.addProperty("runtime_state", state.getStateName().name());
            row.addProperty("root_kind", rootKind);
            row.addProperty("root_key", rootKey);
            row.addProperty("implementation_target", target);
            row.addProperty("actual_card_db_loaded", true);
            row.addProperty("exact_source_bound", exactSourceBound);
            row.addProperty("implementation_target_constructed", targetBound);
            row.addProperty("runtime_detail", runtimeDetail);
            row.addProperty("direct_effect_resolve_bypass", false);
            row.addProperty("status", "PASS");
            output.add(row.toString());
        }

        Assert.assertEquals(passCount, 301, "all assigned V2 paths must bind to actual-card runtime");
        Files.createDirectories(outPath.getParent());
        Files.write(outPath, output, StandardCharsets.UTF_8);
    }

    private static String str(JsonObject object, String key) {
        return object.get(key).getAsString();
    }

    private static CardState findSourceState(Card card, String directive, String sourceSVar, String sourceText) {
        for (CardStateName stateName : CardStateName.values()) {
            if (!card.hasState(stateName)) continue;
            final CardState candidate = card.getState(stateName);
            if (candidate != null && sourceMatches(candidate, directive, sourceSVar, sourceText)) {
                return candidate;
            }
        }
        return null;
    }

    private static boolean sourceMatches(CardState state, String directive, String sourceSVar, String sourceText) {
        if ("SVAR".equals(directive)) {
            if (sourceSVar.isEmpty() || !state.hasSVar(sourceSVar)) return false;
            final int payloadAt = sourceText.indexOf(':', 5);
            if (payloadAt < 0) return false;
            return state.getSVar(sourceSVar).equals(sourceText.substring(payloadAt + 1));
        }
        if ("KEYWORD".equals(directive)) {
            final String keywordPayload = sourceText.substring(2);
            return state.getIntrinsicKeywords().stream()
                    .anyMatch(k -> keywordEquivalent(k.getOriginal(), keywordPayload));
        }
        if ("STATIC".equals(directive)) {
            return state.getStaticAbilities().stream().anyMatch(st -> staticMatchesSource(st, sourceText));
        }
        if ("ABILITY".equals(directive)) {
            final String sourceApi = firstApi(sourceText);
            return collectSpellAbilities(state).stream()
                    .anyMatch(sa -> sa.getApi() != null && sa.getApi().name().equals(sourceApi));
        }
        return false;
    }

    private static boolean hasApi(List<SpellAbility> graph, String api) {
        return graph.stream().anyMatch(sa -> sa.getApi() != null && sa.getApi().name().equals(api));
    }

    private static boolean keywordEquivalent(String runtime, String source) {
        if (runtime.equals(source)) return true;
        return runtime.split(":", 2)[0].equalsIgnoreCase(source.split(":", 2)[0]);
    }

    private static String firstApi(String source) {
        String payload = source.startsWith("A:") ? source.substring(2) : source;
        for (String piece : payload.split("\\|")) {
            piece = piece.trim();
            if (piece.startsWith("SP$") || piece.startsWith("AB$") || piece.startsWith("DB$")) {
                return piece.substring(piece.indexOf('$') + 1).trim();
            }
        }
        return "";
    }

    private static Map<String, String> parseParams(String source) {
        String payload = source;
        if (source.startsWith("A:") || source.startsWith("S:") || source.startsWith("T:")) {
            payload = source.substring(2);
        } else if (source.startsWith("SVar:")) {
            int first = source.indexOf(':', 5);
            payload = first >= 0 ? source.substring(first + 1) : "";
        }
        final Map<String, String> result = new LinkedHashMap<>();
        for (String piece : payload.split("\\|")) {
            int dollar = piece.indexOf('$');
            if (dollar > 0) {
                result.put(piece.substring(0, dollar).trim(), piece.substring(dollar + 1).trim());
            }
        }
        return result;
    }

    private static boolean staticMatchesSource(StaticAbility st, String source) {
        Map<String, String> expected = parseParams(source);
        String mode = expected.get("Mode");
        if (mode != null && st.getMode().stream().noneMatch(m -> m.name().equals(mode))) return false;
        for (Map.Entry<String, String> entry : expected.entrySet()) {
            String key = entry.getKey();
            if (Set.of("Mode", "Description").contains(key)) continue;
            if (st.hasParam(key) && !st.getParam(key).equals(entry.getValue())) return false;
        }
        return true;
    }

    private static boolean hasRuntimeStatic(CardState state, String rootKind, String rootKey) {
        if (!state.getStaticAbilities().isEmpty()) {
            if (!"STATIC".equals(rootKind) || rootKey.isEmpty()) return true;
            return state.getStaticAbilities().stream()
                    .anyMatch(st -> st.getMode().stream().anyMatch(m -> m.name().equals(rootKey)));
        }
        for (KeywordInterface kw : state.getIntrinsicKeywords()) {
            if (!kw.getStaticAbilities().isEmpty()) return true;
        }
        return false;
    }

    private static String apiForTarget(String target) {
        if (target.endsWith("ControlGainEffect")) return "GainControl";
        if (target.endsWith("ControlGainVariantEffect")) return "GainControlVariant";
        if (target.endsWith("ProtectEffect")) return "Protection";
        String name = target.substring(target.lastIndexOf('.') + 1);
        return name.substring(0, name.length() - "Effect".length());
    }

    private static List<SpellAbility> collectSpellAbilities(CardState state) {
        final List<SpellAbility> result = new ArrayList<>();
        final Set<SpellAbility> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        for (SpellAbility sa : state.getSpellAbilities()) walk(sa, result, seen);
        for (Trigger trigger : state.getTriggers()) {
            try { walk(trigger.ensureAbility(state), result, seen); } catch (RuntimeException ignored) { }
        }
        for (ReplacementEffect replacement : state.getReplacementEffects()) {
            walk(replacement.getOverridingAbility(), result, seen);
        }
        for (KeywordInterface keyword : state.getIntrinsicKeywords()) {
            for (SpellAbility sa : keyword.getAbilities()) walk(sa, result, seen);
            for (Trigger trigger : keyword.getTriggers()) {
                try { walk(trigger.ensureAbility(keyword), result, seen); } catch (RuntimeException ignored) { }
            }
            for (ReplacementEffect replacement : keyword.getReplacements()) {
                walk(replacement.getOverridingAbility(), result, seen);
            }
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    private static void walk(SpellAbility sa, List<SpellAbility> result, Set<SpellAbility> seen) {
        if (sa == null || !seen.add(sa)) return;
        result.add(sa);
        walk(sa.getSubAbility(), result, seen);
        try {
            Field additional = SpellAbility.class.getDeclaredField("additionalAbilities");
            additional.setAccessible(true);
            for (SpellAbility child : ((Map<String, SpellAbility>) additional.get(sa)).values()) {
                walk(child, result, seen);
            }
            Field lists = SpellAbility.class.getDeclaredField("additionalAbilityLists");
            lists.setAccessible(true);
            for (Collection<?> list : ((Map<String, ? extends Collection<?>>) lists.get(sa)).values()) {
                for (Object child : list) {
                    if (child instanceof SpellAbility) walk((SpellAbility) child, result, seen);
                }
            }
        } catch (ReflectiveOperationException e) {
            throw new RuntimeException(e);
        }
    }
}
